# models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta


class Client(models.Model):
    company_name = models.CharField(max_length=255)
    # company_id = models.CharField(max_length=100, blank=True, null=True)
    # company_password = models.CharField(max_length=255, blank=True, null=True)
    group = models.CharField(max_length=100, blank=True, null=True)
    account_no = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    # Change email field to a JSONField to store a list of emails
    email = models.JSONField(default=list)      # Store multiple emails as a JSON array
    first_allocated_person = models.CharField(max_length=100, blank=True, null=True)
    review_person = models.CharField(max_length=100, blank=True, null=True)
    # quickbook_status = models.CharField(
    #     max_length=100,
    #     choices=[('done', 'Done'), ('pending', 'Pending'), ('data_provided', 'Data Provided by Client')]
    # )
    year = models.IntegerField(default=2025)
    months = models.JSONField(default=dict)  # Store month number -> person name mappings
    remark = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.company_name


class SignupOTP(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        # OTP expires after 10 minutes
        return self.created_at < timezone.now() - timedelta(minutes=10)

    def __str__(self):
        return f"{self.email} - {self.code} ({'used' if self.is_used else 'active'})"