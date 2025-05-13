"""
Script to ensure media directories exist on application startup.
This is particularly important for Railway deployments where the filesystem is ephemeral.
"""

import os
from pathlib import Path

def ensure_media_dirs():
    """Create all necessary media directories if they don't exist."""
    # Get the base directory
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define media directories to create
    media_dirs = [
        'media',
        'media/candidate_photos',
        'media/temp_faces',
        'media/facial_recognition',
        'media/facial_recognition/face_db',
    ]
    
    # Create each directory
    for directory in media_dirs:
        dir_path = base_dir / directory
        dir_path.mkdir(exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")
    
    return True

if __name__ == "__main__":
    ensure_media_dirs()
