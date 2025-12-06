# core/views.py
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from core.models import Client
from core.forms import ClientForm
from django.http import HttpResponse
import pandas as pd
import openpyxl
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import logging
logger = logging.getLogger(__name__)
import ast


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
        send_mail(subject, message, 'no-reply@yourdomain.com', [email], html_message=message)
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
                messages.success(request, "Your password has been reset successfully.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
        return render(request, 'password_reset_form.html')
    else:
        messages.error(request, "Invalid or expired password reset link.")
        return redirect('login')


def signup_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username')
        # Check if the email already exists in the database
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('signup')
        # Create a new user with a hashed password
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')  # Redirect to login after signup
    return render(request, 'signup.html')  # Render the signup form


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Try to get the user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username  # Use username for authentication
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect('login')
        # Authenticate the user using email and password
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # Log the user in
            return redirect('dashboard')  # Redirect to dashboard after login
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')
    return render(request, 'login.html')  # Render the login form


def dashboard(request):
    return render(request, 'dashboard.html')


# List all clients with search functionality
def client_list(request):
    query = request.GET.get('search', '')
    if query:
        # Split the search query into separate terms
        search_terms = query.split()
        # Initialize a Q object to combine the search conditions
        q_object = Q()
        # Add conditions for each search term to match both company_name and group fields
        for term in search_terms:
            q_object |= Q(company_name__icontains=term) | Q(group__icontains=term)
        # Filter clients based on the combined search conditions
        clients = Client.objects.filter(q_object)
    else:
        clients = Client.objects.all()
    return render(request, 'client_list.html', {'clients': clients})


# Add new client
months_list = [
    ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
    ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
    ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
]

def client_add(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            # Collect month-person mappings (store as a dictionary)
            months_with_names = {}
            for i in range(1, 13):  # Loop through all months (1-12)
                month_key = f"month_person_{i}"
                month_name = request.POST.get(month_key)  # Get entered name for the month
                if month_name:  # Only store months with a name
                    months_with_names[str(i)] = month_name  # Store month number and person name
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
            except:
                # If the input is invalid, we just keep it empty
                email_list = []
            # Save the form and attach the months data (store as dictionary)
            client = form.save(commit=False)
            client.email = email_list  # Store the list of emails as a list
            client.months = months_with_names  # Ensure it stores as a dictionary
            client.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'client_add.html', {'form': form, 'months': months_list})


def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
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
            except:
                # If the input is invalid, we just keep it empty
                email_list = []
            client.email = email_list  # Store the list of emails as a list
            # Initialize a dictionary for months with names
            months_with_names = {}
            # Process the month-person assignments
            for month_num, month_name in months_list:
                checkbox_value = request.POST.getlist('months')  # Use getlist to get all selected months
                if str(month_num) in checkbox_value:
                    person = request.POST.get(f'month_person_{month_num}')
                    if person and person != "None":  # Avoid storing "None" for empty names
                        months_with_names[str(month_num)] = person
                elif str(month_num) in client.months:
                    months_with_names[str(month_num)] = client.months[str(month_num)]
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
def client_delete_select(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'client_delete_select.html', {'client': client})


@login_required
def delete_client(request, client_id):
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to delete this company.")
        return redirect('client_list')  # Or wherever you want to redirect the user
    try:
        client = Client.objects.get(id=client_id)
        client.delete()
        messages.success(request, "Company deleted successfully.")
    except Client.DoesNotExist:
        messages.error(request, "Client not found.")
    return redirect('client_list')


# Search Details View
def search_details(request):
    company = None
    if 'search' in request.GET:
        search_term = request.GET['search']
        # If the search term matches a full company name, perform an exact match search
        if search_term:
            company = Client.objects.filter(company_name__iexact=search_term).first()
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
def search_company(request):
    query = request.GET.get('q', '')
    if query:
        # Check if the query exactly matches a company name
        results = Client.objects.filter(company_name__iexact=query)
        if not results:
            # If no exact match, perform a partial search on company_name, company_id, or account_no
            results = Client.objects.filter(
                Q(company_name__icontains=query) | Q(account_no__icontains=query)
            )
    else:
        results = Client.objects.all()
    return render(request, 'search_results.html', {'results': results})


def import_excel(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        df = pd.read_excel(excel_file)
        # Normalize the column names: Strip spaces and convert to lowercase (optional)
        df.columns = df.columns.str.strip()  # Remove any leading/trailing spaces
        df.columns = df.columns.str.lower()  # Convert all columns to lowercase for consistency
        # Print out the column names for debugging
        print("Excel Columns:", df.columns)
        # Required columns (ensure they match the exact column names in your Excel file)
        required_columns = ['company name']  # Only company_name is required now
        # Check for missing required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
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
                    client_data['months'] = row['month']  # Assuming 'month' is a string or list
                # Handle the optional 'remark' field
                client_data['remark'] = row.get('remark', None)
                # Create a new Client instance and save to the database
                Client.objects.create(**client_data)
            except KeyError as e:
                # In case a specific column still doesn't exist, this will catch the error
                return HttpResponse(f"Error: Missing column or value for {e}")
        return HttpResponse('File imported successfully!')
    return render(request, 'import_excel.html')


def export_excel(request, list_type):
    clients = Client.objects.all()
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.append([
        "Company Name", "Group", "Account No", "First Allocated Person",
        "Review Person", "Year", "Months", "Remark", "Email", "Bank Name"
    ])
    for client in clients:
        # Format months and assigned persons as "Month Number - Person Name"
        months_assigned = []
        if client.months:
            for month_num, person_name in client.months.items():
                month_name = months_list[int(month_num) - 1][1]  # Get month name from the list
                months_assigned.append(f"{month_name} ({person_name})")
        # Join the months and assigned persons with commas
        months_column = ", ".join(months_assigned) if months_assigned else ''
        sheet.append([
            client.company_name,
            client.group or '',
            client.account_no,
            client.first_allocated_person,
            client.review_person,
            client.year,
            months_column,  # Now contains "Month Name (Person)"
            client.remark or '',
            ", ".join(client.email) if client.email else '',
            client.bank_name or ''
        ])
    response = HttpResponse(content_type="application/vnd.openpyxl.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename=client_list.xlsx'
    wb.save(response)
    return response


def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout
