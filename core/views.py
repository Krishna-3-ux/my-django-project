# core/views.py
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import logging
import ast
import random
import os
from datetime import timedelta
import pandas as pd
import openpyxl
from core.models import Client, SignupOTP
from core.forms import ClientForm

logger = logging.getLogger(__name__)

# Special setup view for deployment (one-time use, should be disabled after setup)


def setup_deployment(request):
    """
    Web-based setup for Render deployment when Shell is not available.
    This should be disabled/removed after initial setup for security.
    """
    method = request.POST if request.method == 'POST' else request.GET

    if method:
        # Check if setup is already done (basic security check)
        setup_key = method.get('setup_key', '')
        expected_key = os.environ.get('SETUP_KEY', 'CHANGE_THIS_IN_PRODUCTION')

        if setup_key != expected_key:
            messages.error(request, "Invalid setup key.")
            return render(request, 'core/setup_deployment.html')

        action = method.get('action')

        if action == 'migrate':
            try:
                from django.core.management import call_command
                call_command('migrate', verbosity=0, interactive=False)
                messages.success(
                    request, "✓ Migrations completed successfully!")
            except Exception as e:
                messages.error(request, f"✗ Migration error: {str(e)}")
                logger.error(f"Migration error: {e}")

        elif action == 'create_superuser':
            username = method.get('username', '').strip()
            email = method.get('email', '').strip()
            password = method.get('password', '')

            if not all([username, email, password]):
                messages.error(request, "All fields are required.")
                return render(request, 'core/setup_deployment.html')

            try:
                if User.objects.filter(username=username).exists():
                    messages.warning(
                        request, f"User '{username}' already exists.")
                else:
                    User.objects.create_superuser(
                        username=username, email=email, password=password)
                    messages.success(
                        request, f"✓ Superuser '{username}' created successfully!")
            except Exception as e:
                messages.error(
                    request, f"✗ Error creating superuser: {str(e)}")
                logger.error(f"Superuser creation error: {e}")

        return render(request, 'core/setup_deployment.html')

    return render(request, 'core/setup_deployment.html')


def _throttle(request, name: str, limit: int, window_seconds: int) -> bool:
    """
    Simple per-IP throttle using Django cache.
    Returns True if the caller exceeded the limit within the window.
    """
    ip = request.META.get("REMOTE_ADDR", "")
    key = f"throttle:{name}:{ip}"
    now = timezone.now().timestamp()
    data = cache.get(key, {"count": 0, "start": now})
    # reset window if expired
    if now - data.get("start", now) > window_seconds:
        data = {"count": 0, "start": now}
    data["count"] += 1
    cache.set(key, data, timeout=window_seconds)
    return data["count"] > limit


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No user with this email found.")
            return render(request, 'core/forgot_password.html')
        # Generate token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))
        # Create password reset link
        reset_link = f"{request.scheme}://{get_current_site(request).domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
        # Render the email template with user info
        subject = "Password Reset Request"
        message = render_to_string('core/password_reset_email.html', {
            'user': user,
            'reset_link': reset_link,
        })
        # Send email
        send_mail(subject, message, 'no-reply@yourdomain.com',
                  [email], html_message=message)
        messages.success(request, "Password reset email sent!")
        return redirect('login')
    return render(request, 'core/forgot_password.html')


# Password Reset Confirm View
def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode('utf-8')
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if password == confirm_password:
                user.set_password(password)
                user.save()
                messages.success(
                    request, "Your password has been reset successfully.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
        return render(request, 'password_reset_form.html')
    else:
        messages.error(request, "Invalid or expired password reset link.")
        return redirect('login')


def signup_view(request):
    """
    Two-step signup with OTP verification:
    1) User enters name + email and clicks "Send OTP".
    2) User enters the OTP and password, then clicks "Create Account".
    """
    # Default values for pre-filling username and email
    prefill_username = ''
    prefill_email = ''
    otp_sent = False

    if request.method == "POST":
        email = (request.POST.get('email') or '').strip()
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        otp = (request.POST.get('otp') or '').strip()

        # Common pre-check: reject if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('signup')

        # Step 1: Send OTP
        if 'send_otp' in request.POST:
            if not email or not username:
                messages.error(
                    request, "Please enter your name and email before requesting OTP.")
                return redirect('signup')

            code = f"{random.randint(100000, 999999):06d}"
            SignupOTP.objects.create(email=email, code=code)

            # Send the OTP to the fixed approver email
            try:
                # Log which email backend is being used (for debugging)
                email_backend = getattr(settings, 'EMAIL_BACKEND', 'Unknown')
                logger.info(f"Using email backend: {email_backend}")
                
                send_mail(
                    subject="Signup OTP Verification",
                    message=f"Signup request for {email}.\nOTP: {code}\nValid for 10 minutes.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=["Swetang@parikhllc.com"],
                    fail_silently=False,
                )
                logger.info(f"OTP email sent successfully to Swetang@parikhllc.com")
            except Exception as e:
                logger.error(f"Failed to send OTP email: {e}")
                error_msg = str(e)
                if "Authentication Required" in error_msg or "gsmtp" in error_msg:
                    messages.error(
                        request, "Email service not configured. Please set SENDGRID_API_KEY in Render environment variables.")
                else:
                    messages.error(
                        request, f"Could not send OTP. Error: {error_msg}")
                return redirect('signup')

            messages.success(
                request, "OTP sent to verifier email. Enter it below to create your account.")
            return render(request, 'signup.html', {
                'prefill_email': email,
                'prefill_username': username,
                'otp_sent': True,
            })

        # Step 2: Verify OTP and create account
        if 'create_account' in request.POST:
            if not otp:
                messages.error(
                    request, "Please enter the OTP sent to the verifier email.")
                return redirect('signup')

            otp_obj = SignupOTP.objects.filter(
                email=email, code=otp, is_used=False
            ).order_by('-created_at').first()

            if not otp_obj or otp_obj.is_expired():
                messages.error(
                    request, "Invalid or expired OTP. Please request a new one.")
                return redirect('signup')

            otp_obj.is_used = True
            otp_obj.save(update_fields=['is_used'])

            # Validate OTP format server-side (6 digits)
            if not (otp.isdigit() and len(otp) == 6):
                messages.error(request, "OTP must be 6 digits.")
                return redirect('signup')

            # Create the user
            user = User.objects.create_user(
                username=username, email=email, password=password)
            user.save()
            messages.success(
                request, "Account created successfully! Please log in.")
            return redirect('login')

    # GET or fallback
    return render(request, 'signup.html', {
        'prefill_username': prefill_username,
        'prefill_email': prefill_email,
        'otp_sent': otp_sent,
    })


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if user exists with this email
        try:
            # or CustomUser if you are using that
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

        # Authenticate using username (Django authenticates with username internally)
        user = authenticate(
            request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)   # Login without any approval check
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'login.html')


@login_required
def manage_users(request):
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('dashboard')

    employees_qs = User.objects.filter(is_superuser=False)
    total_employees = employees_qs.count()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user_to_delete = get_object_or_404(employees_qs, pk=user_id)
        user_to_delete.delete()
        messages.success(request, "Employee deleted successfully.")
        return redirect('manage_users')

    return render(request, 'manage_users.html', {
        'employees': employees_qs.order_by('username'),
        'total_employees': total_employees,
    })


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


# List all clients with search functionality
@login_required
def client_list(request):
    query = request.GET.get('search', '')
    if query:
        # Split the search query into separate terms
        search_terms = query.split()
        # Initialize a Q object to combine the search conditions
        q_object = Q()
        # Add conditions for each search term to match both company_name and group fields
        for term in search_terms:
            q_object |= Q(company_name__icontains=term) | Q(
                group__icontains=term)
        # Filter clients based on the combined search conditions
        clients = Client.objects.filter(q_object)
    else:
        clients = Client.objects.all()
    return render(request, 'client_list.html', {'clients': clients})


# Define months list at module level for reuse across functions
MONTHS_LIST = [
    ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
    ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
    ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
]


@login_required
def client_add(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            # Collect month-person mappings (store as a dictionary)
            months_with_names = {}
            for i in range(1, 13):  # Loop through all months (1-12)
                month_key = f"month_person_{i}"
                # Get entered name for the month
                month_name = request.POST.get(month_key)
                if month_name:  # Only store months with a name
                    # Store month number and person name
                    months_with_names[str(i)] = month_name
            # Handle email input
            email_input = request.POST.get('email', '')
            try:
                # Convert the string to a proper list (safely)
                email_list = ast.literal_eval(email_input)
                if isinstance(email_list, list):
                    # Ensure all items are strings (if not, set to empty list)
                    email_list = [str(email).strip() for email in email_list]
                else:
                    email_list = []
            except (ValueError, SyntaxError) as e:
                # If the input is invalid, we just keep it empty
                logger.warning(f"Invalid email input format: {e}")
                email_list = []
            # Save the form and attach the months data (store as dictionary)
            client = form.save(commit=False)
            client.email = email_list  # Store the list of emails as a list
            client.months = months_with_names  # Ensure it stores as a dictionary
            client.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'client_add.html', {'form': form, 'months': MONTHS_LIST})


@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    # Convert MONTHS_LIST format for this view (needs integer keys)
    months_list = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    # Ensure client.months is initialized as a dictionary (it could be None or a string)
    if not isinstance(client.months, dict):
        client.months = {}

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            # Handle email input
            email_input = request.POST.get('email', '')
            try:
                # Convert the string to a proper list (safely)
                email_list = ast.literal_eval(email_input)
                if isinstance(email_list, list):
                    # Ensure all items are strings (if not, set to empty list)
                    email_list = [str(email).strip() for email in email_list]
                else:
                    email_list = []
            except (ValueError, SyntaxError) as e:
                # If the input is invalid, we just keep it empty
                logger.warning(f"Invalid email input format: {e}")
                email_list = []
            client.email = email_list  # Store the list of emails as a list
            # Initialize a dictionary for months with names
            months_with_names = {}
            # Process the month-person assignments
            for month_num, month_name in months_list:
                # Use getlist to get all selected months
                checkbox_value = request.POST.getlist('months')
                if str(month_num) in checkbox_value:
                    person = request.POST.get(f'month_person_{month_num}')
                    if person and person != "None":  # Avoid storing "None" for empty names
                        months_with_names[str(month_num)] = person
                elif str(month_num) in client.months:
                    months_with_names[str(month_num)
                                      ] = client.months[str(month_num)]
            # Update the client object with the modified month-person mappings
            client.months = months_with_names
            client.save()
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'client_update.html', {
        'form': form,
        'client': client,
        'months_list': months_list,
    })


# Delete client (confirmation page)
@login_required
def client_delete_select(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'client_delete_select.html', {'client': client})


@login_required
def delete_client(request, client_id):
    if not request.user.is_superuser:
        messages.error(
            request, "You are not authorized to delete this company.")
        # Or wherever you want to redirect the user
        return redirect('client_list')
    try:
        client = Client.objects.get(id=client_id)
        client.delete()
        messages.success(request, "Company deleted successfully.")
    except Client.DoesNotExist:
        messages.error(request, "Client not found.")
    return redirect('client_list')


# Search Details View
@login_required
def search_details(request):
    company = None
    if 'search' in request.GET:
        search_term = request.GET['search']
        # If the search term matches a full company name, perform an exact match search
        if search_term:
            company = Client.objects.filter(
                company_name__iexact=search_term).first()
        # If no exact match is found, proceed with partial search by company_name only
        if not company:
            search_terms = search_term.split()
            # Initialize a Q object to combine conditions for the search terms
            q_object = Q()
            # Add conditions for each term to match company_name with better handling of word order
            for term in search_terms:
                q_object &= Q(company_name__icontains=term)
            # Perform the search and get the first matching company
            company = Client.objects.filter(q_object).first()
    months_list = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    return render(request, 'search_details.html', {
        'company': company,
        'months_list': months_list,  # Pass months_list here
    })


# Search for companies (simple search results view)
@login_required
def search_company(request):
    query = request.GET.get('q', '')
    if query:
        # Check if the query exactly matches a company name
        results = Client.objects.filter(company_name__iexact=query)
        if not results:
            # If no exact match, perform a partial search on company_name, company_id, or account_no
            results = Client.objects.filter(
                Q(company_name__icontains=query) | Q(
                    account_no__icontains=query)
            )
    else:
        results = Client.objects.all()
    return render(request, 'search_results.html', {'results': results})


@login_required
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        # Validate file type
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(
                request, "Invalid file type. Please upload an Excel file (.xlsx or .xls)")
            return render(request, 'import_excel.html')
        # Validate file size (max 10MB)
        if excel_file.size > 10 * 1024 * 1024:
            messages.error(
                request, "File size too large. Maximum size is 10MB")
            return render(request, 'import_excel.html')
        try:
            df = pd.read_excel(excel_file)  # This line should be indented
        except Exception as e:
            messages.error(request, f"Error reading Excel file: {str(e)}")
            return render(request, 'import_excel.html')
        
        # Normalize the column names: Strip spaces and convert to lowercase (optional)
        df.columns = df.columns.str.strip()  # Remove any leading/trailing spaces
        # Convert all columns to lowercase for consistency
        df.columns = df.columns.str.lower()
        # Print out the column names for debugging
        print("Excel Columns:", df.columns)
        # Required columns (ensure they match the exact column names in your Excel file)
        # Only company_name is required now
        required_columns = ['company name']
        # Check for missing required columns
        missing_columns = [
            col for col in required_columns if col not in df.columns]
        if missing_columns:
            return HttpResponse(f"Missing columns: {', '.join(missing_columns)}")
        
        # Iterate through the rows and save the data to the database
        for index, row in df.iterrows():
            try:
                # Extract data from the row
                client_data = {
                    'company_name': row['company name'],
                    'bank_name': row.get('bank name', None),
                    'group': row.get('group', None),
                    'account_no': row.get('account no', None),
                    'first_allocated_person': row.get('first allocated person', None),
                    'review_person': row.get('review person', None),
                }
                # Optional fields: 'year' and 'month'
                if 'year' in df.columns:
                    client_data['year'] = row['year']
                if 'month' in df.columns:
                    # Assuming 'month' is a string or list
                    client_data['months'] = row['month']
                # Handle the optional 'remark' field
                client_data['remark'] = row.get('remark', None)
                # Create a new Client instance and save to the database
                Client.objects.create(**client_data)
            except KeyError as e:
                # In case a specific column still doesn't exist, this will catch the error
                messages.error(
                    request, f"Error: Missing column or value for {e}")
                return render(request, 'import_excel.html')
            except Exception as e:
                logger.error(f"Error creating client at row {index}: {e}")
                messages.error(
                    request, f"Error processing row {index + 1}: {str(e)}")
                return render(request, 'import_excel.html')
        
        messages.success(request, 'File imported successfully!')
        return redirect('client_list')
    
    return render(request, 'import_excel.html')


@login_required
def export_excel(request, list_type):
    clients = Client.objects.all()
    wb = openpyxl.Workbook()
    sheet = wb.active

    sheet.append([
        "Company Name", "Group", "Account No", "First Allocated Person",
        "Review Person", "Year", "Months", "Remark", "Email", "Bank Name"
    ])

    for client in clients:
        # Format months and assigned persons safely
        months_assigned = []

        if client.months:
            for month_num, person_name in client.months.items():
                try:
                    num = int(month_num)
                    if 1 <= num <= len(MONTHS_LIST):
                        month_name = MONTHS_LIST[num - 1][1]
                        months_assigned.append(f"{month_name} ({person_name})")
                    else:
                        continue  # skip invalid month numbers
                except (ValueError, TypeError, IndexError) as e:
                    logger.warning(
                        f"Invalid month format for client {client.id}: {e}")
                    continue  # skip invalid month formats

        months_column = ", ".join(months_assigned) if months_assigned else ''

        sheet.append([
            client.company_name,
            client.group or '',
            client.account_no,
            client.first_allocated_person,
            client.review_person,
            client.year,
            months_column,
            client.remark or '',
            ", ".join(client.email) if client.email else '',
            client.bank_name or ''
        ])

    response = HttpResponse(
        content_type="application/vnd.openpyxl.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename=client_list.xlsx'
    wb.save(response)
    return response


def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout
