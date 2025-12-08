from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from core.models import SignupOTP


class Command(BaseCommand):
    help = "Delete used OTPs and OTPs older than 10 minutes."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=10)
        qs = SignupOTP.objects.filter(Q(is_used=True) | Q(created_at__lt=cutoff))
        count = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} expired/used OTP(s)."))

