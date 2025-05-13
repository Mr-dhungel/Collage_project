"""
Advanced Facial Recognition Module using MTCNN for face detection and InceptionResNetV1 for face recognition.

This module provides a class for high-accuracy facial recognition operations using PyTorch-based
models. It uses MTCNN from facenet_pytorch for face detection and InceptionResNetV1 with VGGFace2
weights for generating face embeddings.

The embeddings are stored as .npy files in the specified database directory, with filenames
corresponding to user IDs. This implementation offers higher accuracy than the basic implementation
and can utilize GPU acceleration when available.
"""

import os
import numpy as np
from PIL import Image
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine
import cv2

class AdvancedFacialRecognition:
    """
    A class for facial recognition using MTCNN for face detection and InceptionResNetV1 for face embedding.

    Attributes:
        detector (MTCNN): MTCNN model for face detection
        model (InceptionResnetV1): InceptionResNetV1 model for face embedding
        db_path (str): Path to the directory containing face database
        face_db (dict): Dictionary containing face embeddings for registered users
        threshold (float): Similarity threshold for face matching
        device (torch.device): Device to run the models on (CPU or CUDA)
    """

    def __init__(self, db_path='facial_recognition/face_db', threshold=0.7, image_size=160, min_face_size=20):
        """
        Initialize the AdvancedFacialRecognition class.

        Args:
            db_path (str): Path to the directory containing face database
            threshold (float): Similarity threshold for face matching (higher is stricter)
            image_size (int): Size of the face images
            min_face_size (int): Minimum size of faces to detect
        """
        # Set device (use GPU if available)
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

        # Initialize MTCNN detector with custom parameters
        self.detector = MTCNN(
            image_size=image_size,
            margin=0,
            min_face_size=min_face_size,
            thresholds=[0.6, 0.7, 0.7],  # MTCNN thresholds
            factor=0.709,
            post_process=True,
            device=self.device
        )

        # Initialize InceptionResNetV1 model with VGGFace2 weights
        self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)

        # Set parameters
        self.image_size = image_size
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
            img_array (numpy.ndarray): Input image as numpy array (RGB)

        Returns:
            list: List of detected face bounding boxes and probabilities
        """
        # Convert numpy array to PIL Image
        img_pil = Image.fromarray(img_array)

        # Detect faces
        boxes, probs = self.detector.detect(img_pil, landmarks=False)

        if boxes is None:
            return []

        # Format results similar to MTCNN from TensorFlow
        results = []
        for box, prob in zip(boxes, probs):
            if prob > 0.9:  # Only include high-confidence detections
                x1, y1, x2, y2 = box
                results.append({
                    'box': [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
                    'confidence': float(prob),
                    'keypoints': {}  # We're not using keypoints here
                })

        return results

    def extract_face(self, img_array, face_box):
        """
        Extract a face from an image based on bounding box.

        Args:
            img_array (numpy.ndarray): Input image as numpy array
            face_box (dict): Face bounding box from detect_face

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
        face_image = face_image.resize((self.image_size, self.image_size))
        face_array = np.asarray(face_image)

        return face_array

    def get_embedding(self, face_array):
        """
        Generate embedding for a face using InceptionResNetV1.

        Args:
            face_array (numpy.ndarray): Face image as numpy array

        Returns:
            numpy.ndarray: Face embedding vector
        """
        # Convert to PIL Image
        face_image = Image.fromarray(face_array)

        # Convert to tensor and normalize
        # Use the MTCNN extract_face method to get a properly formatted tensor
        # This is a workaround since the transform method is not available
        face_tensor = self.detector(face_image, return_prob=False).unsqueeze(0).to(self.device)

        # Get embedding
        with torch.no_grad():
            embedding = self.model(face_tensor).cpu().numpy()

        return embedding[0]

    def register_face(self, user_id, img_path=None, img_array=None):
        """
        Register a face in the database. If the user already exists, compute the mean
        of the existing embedding and the new one for better accuracy.

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
        new_embedding = self.get_embedding(face_array)

        # Check if user already exists in the database
        if user_id in self.face_db:
            # Get existing embedding
            existing_embedding = self.face_db[user_id]

            # Compute mean embedding (average of existing and new)
            embedding = (existing_embedding + new_embedding) / 2.0

            # Normalize the embedding to unit length
            embedding = embedding / np.linalg.norm(embedding)
        else:
            # This is a new user, use the new embedding directly
            embedding = new_embedding

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
        best_score = 0.0  # Initialize with worst possible score (for cosine similarity, higher is better)

        for user_id, db_embedding in self.face_db.items():
            # Calculate cosine similarity (higher is more similar)
            similarity = 1 - cosine(embedding, db_embedding)  # Convert distance to similarity

            if similarity > best_score:
                best_score = similarity
                best_match = user_id

        # Check if the best match is above the threshold
        if best_match is not None and best_score >= self.threshold:
            return best_match, best_score
        else:
            return None, best_score
