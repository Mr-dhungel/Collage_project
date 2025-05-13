#!/bin/bash

# Exit on error
set -o errexit

echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Change to core directory
echo "Changing to core directory..."
cd core

# Collect static files only during build
echo "Collecting static files..."
python manage.py collectstatic --no-input
