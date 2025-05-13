"""
Facial Recognition package for the Voting System.
This package provides facial recognition functionality using either the simple or advanced implementation.
"""

# Import the facial recognition implementations
try:
    from .advanced_face_recognition import AdvancedFacialRecognition as FacialRecognition
    USING_ADVANCED = True
    print("Using Advanced Facial Recognition with InceptionResNetV1 (VGGFace2)")
except ImportError:
    from .face_recognition import FacialRecognition
    USING_ADVANCED = False
    print("Using Simple Facial Recognition with ResNet50")

__all__ = ['FacialRecognition', 'USING_ADVANCED']
