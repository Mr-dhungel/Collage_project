#!/bin/bash

# Exit on error
set -o errexit

echo "Starting build process..."

# Set environment variable to indicate we're in Railway
export RAILWAY_ENVIRONMENT=production

# Install system dependencies if apt-get is available
if command -v apt-get &> /dev/null; then
    echo "Installing system dependencies..."
    apt-get update -y
    apt-get install -y --no-install-recommends \
        python3-dev python3-pip libsm6 libxext6 libxrender-dev libglib2.0-0 \
        libgl1-mesa-glx libgl1 libglu1-mesa libglu1 libpq-dev build-essential \
        cmake pkg-config libx11-dev libatlas-base-dev libgtk-3-dev libgtk2.0-dev \
        libboost-python-dev libjpeg-dev libpng-dev libtiff-dev ffmpeg \
        libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev \
        libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev \
        libpango1.0-dev libhdf5-dev libhdf5-serial-dev libhdf5-103 \
        libeigen3-dev libopenblas-dev liblapack-dev
    apt-get clean
    rm -rf /var/lib/apt/lists/*
else
    echo "Warning: apt-get not available, skipping system dependencies installation"
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
