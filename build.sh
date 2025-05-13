#!/bin/bash

# Exit on error
set -o errexit

echo "Starting build process..."

# Set environment variable to indicate we're in Railway
export RAILWAY_ENVIRONMENT=production

# Install system dependencies if apt.txt exists
if [ -f "apt.txt" ]; then
    echo "Installing system dependencies from apt.txt..."
    if command -v apt-get &> /dev/null; then
        apt-get update -y
        xargs -a apt.txt apt-get install -y
    else
        echo "Warning: apt-get not available, skipping system dependencies installation"
    fi
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p core/media/facial_recognition/face_db
mkdir -p core/media/candidate_photos
mkdir -p core/media/temp_faces

# Change to core directory
echo "Changing to core directory..."
cd core

# Collect static files only during build
echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Build process completed successfully."
