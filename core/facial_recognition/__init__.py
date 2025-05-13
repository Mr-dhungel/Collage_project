"""
Facial Recognition package for the Voting System.
This package provides facial recognition functionality using either the simple or advanced implementation.
"""

import os
import sys

# Check if we're in a production environment (Railway)
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'

# Define a dummy FacialRecognition class for environments where OpenCV is not available
class DummyFacialRecognition:
    """A dummy implementation of FacialRecognition for environments where OpenCV is not available."""

    def __init__(self, *args, **kwargs):
        print("WARNING: Using dummy facial recognition implementation. OpenCV is not available.")

    def detect_faces(self, *args, **kwargs):
        return []

    def create_embedding(self, *args, **kwargs):
        return None

    def compare_embeddings(self, *args, **kwargs):
        return 0.0

# Import the facial recognition implementations
try:
    # First try to import OpenCV to check if it's available
    import cv2

    try:
        from .advanced_face_recognition import AdvancedFacialRecognition as FacialRecognition
        USING_ADVANCED = True
        print("Using Advanced Facial Recognition with InceptionResNetV1 (VGGFace2)")
    except ImportError:
        from .face_recognition import FacialRecognition
        USING_ADVANCED = False
        print("Using Simple Facial Recognition with ResNet50")
except ImportError:
    # If OpenCV is not available, use the dummy implementation
    FacialRecognition = DummyFacialRecognition
    USING_ADVANCED = False
    print("WARNING: OpenCV is not available. Using dummy facial recognition implementation.")

    # Only raise an error in development environment
    if not IS_PRODUCTION:
        print("ERROR: OpenCV is required for facial recognition. Please install the required dependencies.")
        print("See the apt.txt file for the required system dependencies.")

__all__ = ['FacialRecognition', 'USING_ADVANCED']
