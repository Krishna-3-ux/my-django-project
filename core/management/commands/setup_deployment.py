"""
Management command to setup deployment (run migrations and create superuser).
Can be called via web interface for free tier users.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import sys


class Command(BaseCommand):
    help = 'Setup deployment: run migrations and optionally create superuser'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a superuser account',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Superuser username',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Superuser email',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Superuser password (required if --create-superuser)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Running migrations...')
        try:
            call_command('migrate', verbosity=1, interactive=False)
            self.stdout.write(self.style.SUCCESS('✓ Migrations completed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Migration error: {e}'))
            sys.exit(1)

        if options['create_superuser']:
            if not options['password']:
                self.stdout.write(self.style.ERROR('✗ --password is required when creating superuser'))
                sys.exit(1)

            username = options['username']
            email = options['email']
            password = options['password']

            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User "{username}" already exists. Skipping.'))
            else:
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f'✓ Superuser "{username}" created successfully'))

