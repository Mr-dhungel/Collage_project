"""
Script to fix the admin user's status and remove any facial recognition data.
"""

import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voting_system.settings')
django.setup()

from accounts.models import User
from voting.models import VotingVoter, Vote

def fix_admin_user():
    try:
        # Get the admin user
        admin_users = User.objects.filter(is_admin=True)
        
        if not admin_users.exists():
            print("No admin users found.")
            return
        
        for admin in admin_users:
            print(f"Fixing admin user: {admin.username}")
            
            # Set is_voter to False
            admin.is_voter = False
            
            # Clear facial recognition data
            admin.has_face_data = False
            admin.face_samples_count = 0
            
            # Save changes
            admin.save()
            
            # Remove admin from voting assignments
            voting_assignments = VotingVoter.objects.filter(voter=admin)
            if voting_assignments.exists():
                count = voting_assignments.count()
                voting_assignments.delete()
                print(f"Removed {count} voting assignments for admin.")
            
            # Remove any votes cast by admin
            votes = Vote.objects.filter(voter=admin)
            if votes.exists():
                count = votes.count()
                votes.delete()
                print(f"Removed {count} votes cast by admin.")
            
            # Remove facial recognition data file if it exists
            if admin.voter_id:
                face_db_path = 'facial_recognition/face_db'
                face_file = os.path.join(face_db_path, f"{admin.voter_id}.npy")
                if os.path.exists(face_file):
                    os.remove(face_file)
                    print(f"Removed facial recognition data file: {face_file}")
            
            print(f"Admin user {admin.username} fixed successfully.")
    
    except Exception as e:
        print(f"Error fixing admin user: {e}")

if __name__ == "__main__":
    fix_admin_user()
