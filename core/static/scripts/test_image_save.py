"""
Test script to check if we can save images to the media directory.
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

def test_image_save():
    """Test if we can save images to the media directory."""
    # Create a simple test image (black image with a white circle)
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 100, (255, 255, 255), -1)
    
    # Create the media directory if it doesn't exist
    media_dir = Path('media')
    media_dir.mkdir(exist_ok=True)
    
    # Create the temp_faces directory if it doesn't exist
    temp_faces_dir = media_dir / 'temp_faces'
    temp_faces_dir.mkdir(exist_ok=True)
    
    # Save the image
    temp_path = temp_faces_dir / 'test_image.jpg'
    success = cv2.imwrite(str(temp_path), img)
    
    if success:
        print(f"✓ Image saved successfully to {temp_path}")
        
        # Check if the file exists
        if temp_path.exists():
            print(f"✓ File exists at {temp_path}")
            
            # Get the file size
            file_size = temp_path.stat().st_size
            print(f"✓ File size: {file_size} bytes")
            
            # Try to read the image
            img_read = cv2.imread(str(temp_path))
            if img_read is not None:
                print(f"✓ Image read successfully from {temp_path}")
                print(f"✓ Image shape: {img_read.shape}")
            else:
                print(f"✗ Failed to read image from {temp_path}")
        else:
            print(f"✗ File does not exist at {temp_path}")
    else:
        print(f"✗ Failed to save image to {temp_path}")
    
    return success

if __name__ == "__main__":
    print("Testing image save...")
    test_image_save()
