# forms.py
from django import forms
from core.models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'company_name', 'company_id', 'company_password', 'group', 'account_no', 
            'bank_name', 'email', 'first_allocated_person', 'review_person', 'quickbook_status', 
            'year', 'months', 'remark'
        ]
    company_name = forms.CharField(max_length=255, required=True)
    company_id = forms.CharField(max_length=100, required=False)
    company_password = forms.CharField(max_length=255, required=False)
    group = forms.CharField(max_length=100, required=False)
    account_no = forms.CharField(max_length=100, required=True)
    # Make the 'bank_name' optional
    bank_name = forms.CharField(max_length=100, required=False)  # Optional field for bank name
    email = forms.CharField(required=False, widget=forms.Textarea, help_text="Enter multiple emails separated by commas")
    first_allocated_person = forms.CharField(max_length=100, required=True)
    review_person = forms.CharField(max_length=100, required=True)
    quickbook_status = forms.ChoiceField(
        choices=[('done', 'Done'), ('pending', 'Pending'), ('data_provided', 'Data Provided by Client')],
        required=True
    )
    year = forms.IntegerField(initial=2025, required=True)
    months = forms.CharField(widget=forms.HiddenInput(), required=False)
    remark = forms.CharField(max_length=500, required=False, widget=forms.Textarea)
    def clean(self):
        cleaned_data = super().clean()
        # Automatically convert text inputs to uppercase
        for field_name in ['company_name', 'company_id', 'group', 'account_no', 'bank_name', 'first_allocated_person', 'review_person', 'remark']:
            field_value = cleaned_data.get(field_name)
            if field_value:
                cleaned_data[field_name] = field_value.upper()
        return cleaned_data