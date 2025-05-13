"""
Script to create an admin user in the Django application.
This script is meant to be run during the Railway deployment process.
"""

import os
import sys
import django

# Add the core directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
sys.path.insert(0, core_dir)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voting_system.settings')

try:
    django.setup()
    from accounts.models import User
    from django.contrib.auth.hashers import make_password
    print("Django setup successful.")
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

def create_admin_user():
    """Create an admin user if one doesn't exist."""
    try:
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
    except Exception as e:
        print(f"Error creating admin user: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    create_admin_user()
