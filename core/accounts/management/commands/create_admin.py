"""
Django management command to create an admin user.
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from accounts.models import User

class Command(BaseCommand):
    help = 'Creates an admin user if one does not exist'

    def handle(self, *args, **options):
        # Check if an admin user already exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('Admin user already exists.'))
            return

        # Create a new admin user
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')

        User.objects.create(
            username=admin_username,
            password=make_password(admin_password),
            email=admin_email,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            is_admin=True,
            is_voter=False,  # Admin should not be a voter
            voter_id=None  # No voter ID needed for admin
        )

        self.stdout.write(self.style.SUCCESS(f"Admin user '{admin_username}' created successfully."))
