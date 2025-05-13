FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RAILWAY_ENVIRONMENT=production

# Set working directory
WORKDIR /app

# Install system dependencies
COPY apt.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-dev python3-pip libsm6 libxext6 libxrender-dev libglib2.0-0 \
    libgl1-mesa-glx libgl1 libglu1-mesa libglu1 libpq-dev build-essential \
    cmake pkg-config libx11-dev libatlas-base-dev libgtk-3-dev libgtk2.0-dev \
    libboost-python-dev libjpeg-dev libpng-dev libtiff-dev ffmpeg \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev \
    libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev \
    libpango1.0-dev libhdf5-dev libhdf5-serial-dev libhdf5-103 \
    libeigen3-dev libopenblas-dev liblapack-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p core/media/facial_recognition/face_db && \
    mkdir -p core/media/candidate_photos && \
    mkdir -p core/media/temp_faces

# Collect static files
RUN cd core && python manage.py collectstatic --noinput

# Run gunicorn
CMD cd core && gunicorn voting_system.wsgi:application --bind 0.0.0.0:$PORT
