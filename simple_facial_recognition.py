"""
Simple facial recognition module for the voting system.

This module provides a simplified version of the facial recognition functionality using
TensorFlow-based models. It uses MTCNN for face detection and ResNet50 for generating
face embeddings.

The embeddings are stored as .npy files in the specified database directory, with filenames
corresponding to user IDs. This implementation is simpler than the advanced version but
still provides good accuracy for basic use cases.
"""

import os
import numpy as np
from PIL import Image
import tensorflow as tf  # Required for TensorFlow backend
from tensorflow.keras.applications.resnet50 import preprocess_input, ResNet50
from mtcnn import MTCNN
from scipy.spatial.distance import cosine
import cv2

class SimpleFacialRecognition:
    """
    A simplified class for facial recognition using MTCNN for face detection and ResNet50 for face embedding.

    Attributes:
        detector (MTCNN): MTCNN model for face detection
        model (ResNet50): ResNet50 model for face embedding
        db_path (str): Path to the directory containing face database
        face_db (dict): Dictionary containing face embeddings for registered users
        threshold (float): Similarity threshold for face matching
    """

    def __init__(self, db_path='facial_recognition/face_db', threshold=0.5):
        """
        Initialize the SimpleFacialRecognition class.

        Args:
            db_path (str): Path to the directory containing face database
            threshold (float): Similarity threshold for face matching (lower is stricter)
        """
        # Initialize MTCNN detector
        self.detector = MTCNN()

        # Initialize ResNet50 model
        self.model = ResNet50(include_top=False, pooling='avg')

        # Set database path and threshold
        self.db_path = db_path
        self.threshold = threshold

        # Create database directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)

        # Load face database
        self.face_db = {}
        self._load_face_db()

    def _load_face_db(self):
        """Load face embeddings from the database directory."""
        if not os.path.exists(self.db_path):
            return

        for filename in os.listdir(self.db_path):
            if filename.endswith('.npy'):
                user_id = filename.split('.')[0]
                embedding_path = os.path.join(self.db_path, filename)
                self.face_db[user_id] = np.load(embedding_path)

    def detect_face(self, img_array):
        """
        Detect faces in an image using MTCNN.

        Args:
            img_array (numpy.ndarray): Input image as numpy array

        Returns:
            list: List of detected face bounding boxes
        """
        faces = self.detector.detect_faces(img_array)
        return faces

    def extract_face(self, img_array, face_box, required_size=(224, 224)):
        """
        Extract a face from an image based on bounding box.

        Args:
            img_array (numpy.ndarray): Input image as numpy array
            face_box (dict): Face bounding box from MTCNN
            required_size (tuple): Required size for the face image

        Returns:
            numpy.ndarray: Extracted and preprocessed face image
        """
        # Extract face coordinates
        x1, y1, width, height = face_box['box']
        x2, y2 = x1 + width, y1 + height

        # Extract the face
        face = img_array[y1:y2, x1:x2]

        # Resize to required size
        face_image = Image.fromarray(face)
        face_image = face_image.resize(required_size)
        face_array = np.asarray(face_image)

        return face_array

    def get_embedding(self, face_array):
        """
        Get embedding vector for a face image.

        Args:
            face_array (numpy.ndarray): Face image as numpy array

        Returns:
            numpy.ndarray: Embedding vector
        """
        # Expand dimensions to match model input shape
        face_array = np.expand_dims(face_array, axis=0)

        # Preprocess the face image
        face_array = preprocess_input(face_array)

        # Get embedding
        embedding = self.model.predict(face_array)

        return embedding[0]

    def register_face(self, user_id, img_path=None, img_array=None):
        """
        Register a face in the database.

        Args:
            user_id (str): User ID to associate with the face
            img_path (str, optional): Path to the image file
            img_array (numpy.ndarray, optional): Image as numpy array

        Returns:
            bool: True if registration successful, False otherwise
        """
        if img_path is None and img_array is None:
            return False

        # Load image if path is provided
        if img_array is None:
            img = cv2.imread(img_path)
            img_array = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detect faces
        faces = self.detect_face(img_array)
        if not faces:
            return False

        # Use the largest face (assuming it's the main face)
        largest_face = max(faces, key=lambda x: x['box'][2] * x['box'][3])

        # Extract and get embedding
        face_array = self.extract_face(img_array, largest_face)
        embedding = self.get_embedding(face_array)

        # Save embedding to database
        np.save(os.path.join(self.db_path, f"{user_id}.npy"), embedding)

        # Update in-memory database
        self.face_db[user_id] = embedding

        return True

    def recognize_face(self, img_path=None, img_array=None):
        """
        Recognize a face from an image.

        Args:
            img_path (str, optional): Path to the image file
            img_array (numpy.ndarray, optional): Image as numpy array

        Returns:
            tuple: (user_id, confidence) if face recognized, (None, 0) otherwise
        """
        if img_path is None and img_array is None:
            return None, 0

        # Load image if path is provided
        if img_array is None:
            img = cv2.imread(img_path)
            img_array = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detect faces
        faces = self.detect_face(img_array)
        if not faces:
            return None, 0

        # Use the largest face (assuming it's the main face)
        largest_face = max(faces, key=lambda x: x['box'][2] * x['box'][3])

        # Extract and get embedding
        face_array = self.extract_face(img_array, largest_face)
        embedding = self.get_embedding(face_array)

        # Compare with database
        best_match = None
        best_score = 1.0  # Initialize with worst possible score

        for user_id, db_embedding in self.face_db.items():
            # Calculate cosine similarity (lower is more similar)
            similarity = cosine(embedding, db_embedding)

            if similarity < best_score:
                best_score = similarity
                best_match = user_id

        # Check if the best match is below the threshold
        if best_match is not None and best_score < self.threshold:
            return best_match, 1.0 - best_score  # Convert to confidence score (higher is better)
        else:
            return None, 0
