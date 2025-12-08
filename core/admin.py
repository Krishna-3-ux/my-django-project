from django.contrib import admin
from core.models import Client, SignupOTP

# Register your models here.
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'group', 'account_no', 'year', 'first_allocated_person', 'review_person']
    list_filter = ['year', 'group']
    search_fields = ['company_name', 'group', 'account_no']
    readonly_fields = ['email', 'months']  # JSONFields are read-only in admin by default


@admin.register(SignupOTP)
class SignupOTPAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'is_used', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['email', 'code']