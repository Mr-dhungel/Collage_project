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

echo "Release process completed successfully."
