"""
Django management command to fix admin users by ensuring they are not voters.
"""

from django.core.management.base import BaseCommand
from accounts.models import User
from voting.models import VotingVoter, Vote
import os

class Command(BaseCommand):
    help = 'Fixes admin users by ensuring they are not voters'

    def handle(self, *args, **options):
        # Get all admin users
        admin_users = User.objects.filter(is_admin=True)
        
        if not admin_users.exists():
            self.stdout.write(self.style.SUCCESS('No admin users found.'))
            return
        
        for admin in admin_users:
            self.stdout.write(f'Fixing admin user: {admin.username}')
            
            # Set is_voter to False
            admin.is_voter = False
            
            # Clear facial recognition data
            admin.has_face_data = False
            admin.face_samples_count = 0
            
            # Clear voter_id if it exists
            if admin.voter_id:
                admin.voter_id = None
            
            # Save changes
            admin.save()
            
            # Remove admin from voting assignments
            voting_assignments = VotingVoter.objects.filter(voter=admin)
            if voting_assignments.exists():
                count = voting_assignments.count()
                voting_assignments.delete()
                self.stdout.write(f'Removed {count} voting assignments for admin.')
            
            # Remove any votes cast by admin
            votes = Vote.objects.filter(voter=admin)
            if votes.exists():
                count = votes.count()
                votes.delete()
                self.stdout.write(f'Removed {count} votes cast by admin.')
            
            # Remove facial recognition data file if it exists
            face_db_path = os.path.join('media', 'facial_recognition', 'face_db')
            if os.path.exists(face_db_path):
                face_file = os.path.join(face_db_path, f"{admin.username}.npy")
                if os.path.exists(face_file):
                    os.remove(face_file)
                    self.stdout.write(f'Removed facial recognition data file: {face_file}')
            
            self.stdout.write(self.style.SUCCESS(f'Admin user {admin.username} fixed successfully.'))
