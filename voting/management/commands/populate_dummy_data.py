import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from django.conf import settings

from voting.models import Voting, Candidate, VotingVoter, Vote
from accounts.models import User

class Command(BaseCommand):
    help = 'Populates the database with dummy data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--voters', type=int, default=10, help='Number of voters to create')
        parser.add_argument('--votings', type=int, default=6, help='Number of votings to create')
        parser.add_argument('--candidates', type=int, default=4, help='Number of candidates per voting')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before creating new data')

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_data()
            
        self.create_admin_if_not_exists()
        voters = self.create_voters(options['voters'])
        votings = self.create_votings(options['votings'])
        self.create_candidates(votings, options['candidates'])
        self.assign_voters_to_votings(voters, votings)
        self.cast_votes(voters, votings)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database with dummy data'))

    def clear_data(self):
        self.stdout.write('Clearing existing data...')
        Vote.objects.all().delete()
        VotingVoter.objects.all().delete()
        Candidate.objects.all().delete()
        Voting.objects.all().delete()
        User.objects.filter(is_admin=False).delete()
        self.stdout.write(self.style.SUCCESS('Data cleared successfully'))

    def create_admin_if_not_exists(self):
        if not User.objects.filter(is_admin=True).exists():
            User.objects.create_user(
                username='admin',
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_admin=True,
                voter_id='0000'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        else:
            self.stdout.write('Admin user already exists')

    def create_voters(self, count):
        self.stdout.write(f'Creating {count} voters...')
        voters = []
        for i in range(count):
            voter_id = f'{random.randint(1000, 9999)}'
            while User.objects.filter(voter_id=voter_id).exists():
                voter_id = f'{random.randint(1000, 9999)}'
                
            voter = User.objects.create_user(
                username=f'voter{i+1}',
                password='voter123',
                first_name=f'Voter{i+1}',
                last_name=f'User',
                is_admin=False,
                is_voter=True,
                voter_id=voter_id
            )
            voters.append(voter)
            self.stdout.write(f'Created voter: {voter.username} with ID: {voter.voter_id}')
        return voters

    def create_votings(self, count):
        self.stdout.write(f'Creating {count} votings...')
        now = timezone.now()
        votings = []
        
        # Create 2 active votings
        for i in range(2):
            voting = Voting.objects.create(
                title=f'Active Voting {i+1}',
                description=f'This is an active voting that is currently in progress. You can cast your vote now!',
                start_time=now - timedelta(days=1),
                end_time=now + timedelta(days=2)
            )
            votings.append(voting)
            self.stdout.write(f'Created active voting: {voting.title}')
        
        # Create 2 upcoming votings
        for i in range(2):
            voting = Voting.objects.create(
                title=f'Upcoming Voting {i+1}',
                description=f'This is an upcoming voting that will start soon. Get ready to cast your vote!',
                start_time=now + timedelta(days=i+1),
                end_time=now + timedelta(days=i+5)
            )
            votings.append(voting)
            self.stdout.write(f'Created upcoming voting: {voting.title}')
        
        # Create 2 completed votings
        for i in range(2):
            voting = Voting.objects.create(
                title=f'Completed Voting {i+1}',
                description=f'This is a completed voting. The results are now available for viewing.',
                start_time=now - timedelta(days=10),
                end_time=now - timedelta(days=i+1)
            )
            votings.append(voting)
            self.stdout.write(f'Created completed voting: {voting.title}')
        
        return votings

    def create_candidates(self, votings, candidates_per_voting):
        self.stdout.write(f'Creating {candidates_per_voting} candidates for each voting...')
        
        # Create a simple default image for candidates
        img_path = os.path.join(settings.MEDIA_ROOT, 'candidate_photos')
        os.makedirs(img_path, exist_ok=True)
        
        for voting in votings:
            for i in range(candidates_per_voting):
                # Create a simple colored square as a candidate image
                color = random.choice(['red', 'blue', 'green', 'purple', 'orange'])
                img_content = self.generate_colored_image(color)
                
                candidate = Candidate.objects.create(
                    voting=voting,
                    name=f'Candidate {i+1} for {voting.title}',
                    description=f'This is candidate {i+1} for {voting.title}. Vote for me to make a difference!',
                    photo=SimpleUploadedFile(f'candidate_{voting.id}_{i+1}.png', img_content, content_type='image/png')
                )
                self.stdout.write(f'Created candidate: {candidate.name}')

    def generate_colored_image(self, color):
        """Generate a simple colored PNG image"""
        from PIL import Image
        import io
        
        # Create a 100x100 image with the specified color
        img = Image.new('RGB', (100, 100), color=color)
        
        # Save to a bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def assign_voters_to_votings(self, voters, votings):
        self.stdout.write('Assigning voters to votings...')
        for voting in votings:
            # Assign a random subset of voters to each voting
            selected_voters = random.sample(voters, random.randint(max(1, len(voters) // 2), len(voters)))
            for voter in selected_voters:
                VotingVoter.objects.create(voting=voting, voter=voter)
                self.stdout.write(f'Assigned {voter.username} to {voting.title}')

    def cast_votes(self, voters, votings):
        self.stdout.write('Casting votes for completed and active votings...')
        for voting in votings:
            if voting.has_ended() or voting.is_active():
                # Get all voters assigned to this voting
                voting_voters = VotingVoter.objects.filter(voting=voting)
                candidates = list(Candidate.objects.filter(voting=voting))
                
                if not candidates:
                    continue
                
                # For completed votings, have all voters vote
                # For active votings, have some voters vote
                voter_percentage = 1.0 if voting.has_ended() else 0.7
                
                for voting_voter in voting_voters:
                    # Randomly decide if this voter will vote (for active votings)
                    if voting.has_ended() or random.random() < voter_percentage:
                        # Select a random candidate
                        candidate = random.choice(candidates)
                        
                        # Create the vote
                        Vote.objects.create(
                            voter=voting_voter.voter,
                            candidate=candidate,
                            voting=voting
                        )
                        self.stdout.write(f'{voting_voter.voter.username} voted for {candidate.name} in {voting.title}')
