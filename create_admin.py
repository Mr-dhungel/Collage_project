"""
Script to create an admin user in the Django application.
This script is meant to be run during the Railway deployment process.
"""

import os
import django
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voting_system.settings')
django.setup()

from accounts.models import User
from django.contrib.auth.hashers import make_password

def create_admin_user():
    """Create an admin user if one doesn't exist."""
    # Check if an admin user already exists
    if User.objects.filter(is_superuser=True).exists():
        print("Admin user already exists.")
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
        voter_id='0000'  # Default voter ID for admin
    )
    
    print(f"Admin user '{admin_username}' created successfully.")

if __name__ == '__main__':
    # Change to the core directory if not already there
    if os.path.basename(os.getcwd()) != 'core':
        try:
            os.chdir('core')
            print("Changed to core directory.")
        except:
            print("Failed to change to core directory.")
            sys.exit(1)
    
    create_admin_user()
