#!/bin/bash

# Exit on error
set -o errexit

echo "Starting release process..."

# Run the script to update ALLOWED_HOSTS
echo "Updating ALLOWED_HOSTS..."
python update_allowed_hosts.py

# Change to core directory
echo "Changing to core directory..."
cd core

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create admin user
echo "Creating admin user..."
python manage.py create_admin

# Fix admin users to ensure they are not voters
echo "Fixing admin users..."
python manage.py fix_admin_users

echo "Release process completed successfully."
