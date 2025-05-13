from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from unittest.mock import patch
import os

from voting.models import Candidate, Voting

class CandidateImageDeletionTest(TestCase):
    def setUp(self):
        # Create a test voting
        self.voting = Voting.objects.create(
            title="Test Voting",
            description="Test Description",
            start_time=timezone.now() - timezone.timedelta(days=1),
            end_time=timezone.now() + timezone.timedelta(days=1)
        )

        # Create a test image
        self.image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        self.test_image = SimpleUploadedFile(
            name='test_image.gif',
            content=self.image_content,
            content_type='image/gif'
        )

    @patch('django.core.files.storage.FileSystemStorage.delete')
    def test_image_deleted_when_candidate_deleted(self, mock_delete):
        # Create a candidate with an image
        candidate = Candidate.objects.create(
            voting=self.voting,
            name="Test Candidate",
            description="Test Description",
            photo=self.test_image
        )

        # Refresh from database to get the actual saved path
        candidate.refresh_from_db()

        # Store the photo name for later verification
        photo_name = candidate.photo.name

        # Delete the candidate
        candidate.delete()

        # Verify that the delete method was called with the correct file name
        mock_delete.assert_called_once_with(photo_name)

    @patch('django.core.files.storage.FileSystemStorage.delete')
    def test_old_image_deleted_when_candidate_updated(self, mock_delete):
        # Create a candidate with an image
        candidate = Candidate.objects.create(
            voting=self.voting,
            name="Test Candidate",
            description="Test Description",
            photo=self.test_image
        )

        # Refresh from database to get the actual saved path
        candidate.refresh_from_db()

        # Store the original photo name for later verification
        original_photo_name = candidate.photo.name

        # Create a new test image
        new_image_content = b'GIF87a\x02\x00\x02\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x02\x00\x02\x00\x00\x02\x02D\x01\x00;'
        new_test_image = SimpleUploadedFile(
            name='new_test_image.gif',
            content=new_image_content,
            content_type='image/gif'
        )

        # Update the candidate with a new image
        candidate.photo = new_test_image
        candidate.save()

        # Verify that the delete method was called with the original file name
        mock_delete.assert_called_once_with(original_photo_name)
