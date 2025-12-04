# models.py
from django.db import models

class Client(models.Model):
    company_name = models.CharField(max_length=255)
    company_id = models.CharField(max_length=100, blank=True, null=True)
    company_password = models.CharField(max_length=255, blank=True, null=True)
    group = models.CharField(max_length=100, blank=True, null=True)
    account_no = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    # Change email field to a JSONField to store a list of emails
    email = models.JSONField(default=list)      # Store multiple emails as a JSON array
    first_allocated_person = models.CharField(max_length=100)
    review_person = models.CharField(max_length=100)
    quickbook_status = models.CharField(
        max_length=100,
        choices=[('done', 'Done'), ('pending', 'Pending'), ('data_provided', 'Data Provided by Client')]
    )
    year = models.IntegerField(default=2025)
    months = models.JSONField(default=dict)  # Store month number -> person name mappings
    remark = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.company_name