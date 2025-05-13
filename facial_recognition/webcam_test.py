"""
Webcam test script for the facial recognition module.
This script can be run directly to test the facial recognition module with a webcam.
"""

import os
import sys
import numpy as np
import cv2
import time

# Add the parent directory to the path so we can import the facial_recognition module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facial_recognition import FacialRecognition, USING_ADVANCED

def test_with_webcam():
    """Test facial recognition with webcam input."""
    try:
        # Initialize facial recognition
        face_recognizer = FacialRecognition(db_path='facial_recognition/face_db', threshold=0.7)
        print(f"✓ FacialRecognition initialized successfully (Using Advanced: {USING_ADVANCED})")

        # Initialize webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("✗ Could not open webcam")
            return False

        print("\nInstructions:")
        print("1. Press 'r' to register your face (enter user ID in console)")
        print("2. Press 'v' to verify your face")
        print("3. Press 'q' to quit")

        while True:
            # Read frame from webcam
            ret, frame = cap.read()
            if not ret:
                print("✗ Could not read frame from webcam")
                break

            # Convert to RGB (OpenCV uses BGR)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces
            faces = face_recognizer.detect_face(rgb_frame)

            # Draw bounding boxes around faces
            for face in faces:
                x, y, w, h = face['box']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Add confidence score
                confidence = face['confidence']
                cv2.putText(frame, f"Conf: {confidence:.2f}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Display the frame
            cv2.imshow('Facial Recognition Test', frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF

            if key == ord('r'):
                # Register face
                if faces:
                    user_id = input("Enter user ID for registration: ")
                    if user_id:
                        success = face_recognizer.register_face(user_id, img_array=rgb_frame)
                        if success:
                            print(f"✓ Face registered successfully as '{user_id}'")
                        else:
                            print("✗ Face registration failed")
                    else:
                        print("✗ No user ID provided")
                else:
                    print("✗ No face detected for registration")

            elif key == ord('v'):
                # Verify face
                if faces:
                    user_id, confidence = face_recognizer.recognize_face(img_array=rgb_frame)
                    if user_id:
                        print(f"✓ Face recognized as: {user_id} (Confidence: {confidence:.2f})")
                    else:
                        print(f"✗ Face not recognized (Confidence: {confidence:.2f})")
                else:
                    print("✗ No face detected for verification")

            elif key == ord('q'):
                # Quit
                break

        # Release resources
        cap.release()
        cv2.destroyAllWindows()

        return True
    except Exception as e:
        print(f"✗ Error testing with webcam: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing facial recognition with webcam...")
    test_with_webcam()
