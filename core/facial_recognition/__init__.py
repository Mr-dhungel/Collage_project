"""
Facial Recognition package for the Voting System.
This package provides facial recognition functionality using either the simple or advanced implementation.
"""

import os
import sys
import traceback

# Check if we're in a production environment (Railway)
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'

# Define a dummy FacialRecognition class for environments where OpenCV is not available
class DummyFacialRecognition:
    """A dummy implementation of FacialRecognition for environments where OpenCV is not available."""

    def __init__(self, *args, **kwargs):
        print("WARNING: Using dummy facial recognition implementation. OpenCV/OpenGL dependencies are not available.")
        self.db_path = kwargs.get('db_path', 'facial_recognition/face_db')
        self.threshold = kwargs.get('threshold', 0.7)
        # Create database directory if it doesn't exist
        os.makedirs(self.db_path, exist_ok=True)

    def detect_face(self, *args, **kwargs):
        return []

    def detect_faces(self, *args, **kwargs):
        return []

    def extract_face(self, *args, **kwargs):
        return None

    def get_embedding(self, *args, **kwargs):
        return None

    def create_embedding(self, *args, **kwargs):
        return None

    def compare_embeddings(self, *args, **kwargs):
        return 0.0

    def register_face(self, *args, **kwargs):
        return False

    def recognize_face(self, *args, **kwargs):
        return None, 0.0

# Import the facial recognition implementations
try:
    # First try to import OpenCV to check if it's available
    import cv2

    # Test if OpenGL is available by creating a small window
    try:
        if not IS_PRODUCTION:  # Skip this test in production to avoid GUI issues
            test_img = cv2.imread(os.path.join(os.path.dirname(__file__), 'test_img.jpg'))
            if test_img is None:
                # Create a small test image if none exists
                test_img = cv2.cvtColor(cv2.imread(os.path.join(os.path.dirname(__file__), 'test_img.jpg')), cv2.COLOR_BGR2RGB)

        # Try to import the advanced implementation
        try:
            from .advanced_face_recognition import AdvancedFacialRecognition as FacialRecognition
            USING_ADVANCED = True
            print("Using Advanced Facial Recognition with InceptionResNetV1 (VGGFace2)")
        except ImportError as e:
            print(f"Could not import advanced facial recognition: {e}")
            # Fall back to simple implementation
            from .face_recognition import FacialRecognition
            USING_ADVANCED = False
            print("Using Simple Facial Recognition with ResNet50")
    except Exception as e:
        print(f"OpenGL error detected: {e}")
        print("Falling back to dummy implementation due to missing OpenGL libraries")
        FacialRecognition = DummyFacialRecognition
        USING_ADVANCED = False

except ImportError as e:
    # If OpenCV is not available, use the dummy implementation
    FacialRecognition = DummyFacialRecognition
    USING_ADVANCED = False
    print(f"WARNING: OpenCV is not available: {e}")
    print("Using dummy facial recognition implementation.")

    # Only show detailed error in development environment
    if not IS_PRODUCTION:
        print("ERROR: OpenCV is required for facial recognition. Please install the required dependencies.")
        print("See the apt.txt file for the required system dependencies.")
        traceback.print_exc()
except Exception as e:
    # Catch any other exceptions
    FacialRecognition = DummyFacialRecognition
    USING_ADVANCED = False
    print(f"ERROR: Unexpected error initializing facial recognition: {e}")

    if not IS_PRODUCTION:
        traceback.print_exc()

__all__ = ['FacialRecognition', 'USING_ADVANCED']
