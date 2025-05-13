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
    apt-get install -y --no-install-recommends $(cat apt.txt) && \
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
