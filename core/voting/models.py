from django.db import models
from django.conf import settings
from django.utils import timezone
import pytz

class Post(models.Model):
    """
    Represents a position that candidates can run for in a voting event.

    Examples include President, Vice President, Secretary, etc.
    Each post belongs to a specific voting event.
    """
    voting = models.ForeignKey('Voting', on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text="Order in which this post appears in the voting form")

    class Meta:
        ordering = ['order', 'title']
        unique_together = ('voting', 'title')

    def __str__(self):
        return f"{self.title} - {self.voting.title}"

class Voting(models.Model):
    """
    Represents a voting event with a defined start and end time.

    A voting contains candidates that voters can vote for. The voting
    has a lifecycle (upcoming, active, completed) based on the current time
    relative to its start and end times.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Votings"

    def __str__(self):
        return self.title

    def _ensure_timezone_aware(self, dt):
        """
        Helper method to ensure datetime is timezone-aware.

        Args:
            dt (datetime): The datetime object to check

        Returns:
            datetime: A timezone-aware datetime object
        """
        if timezone.is_naive(dt):
            return timezone.make_aware(dt)
        return dt

    def is_active(self):
        """
        Check if the voting is currently active.

        A voting is active if the current time is between the start and end times.
        All times are converted to UTC for consistent comparison.

        Returns:
            bool: True if the voting is active, False otherwise
        """
        now = timezone.now()
        # Make sure both times are in UTC for comparison
        start_time = self._ensure_timezone_aware(self.start_time)
        end_time = self._ensure_timezone_aware(self.end_time)

        # Convert all to UTC for consistent comparison
        now_utc = now.astimezone(pytz.UTC)
        start_utc = start_time.astimezone(pytz.UTC)
        end_utc = end_time.astimezone(pytz.UTC)

        return start_utc <= now_utc <= end_utc

    def has_ended(self):
        """
        Check if the voting has ended.

        A voting has ended if the current time is after the end time.
        All times are converted to UTC for consistent comparison.

        Returns:
            bool: True if the voting has ended, False otherwise
        """
        now = timezone.now()
        end_time = self._ensure_timezone_aware(self.end_time)

        # Convert to UTC for consistent comparison
        now_utc = now.astimezone(pytz.UTC)
        end_utc = end_time.astimezone(pytz.UTC)

        # Add a small buffer (1 second) to prevent edge cases
        return now_utc > end_utc

    def has_started(self):
        """
        Check if the voting has started.

        A voting has started if the current time is after or equal to the start time.
        All times are converted to UTC for consistent comparison.

        Returns:
            bool: True if the voting has started, False otherwise
        """
        now = timezone.now()
        start_time = self._ensure_timezone_aware(self.start_time)

        # Convert to UTC for consistent comparison
        now_utc = now.astimezone(pytz.UTC)
        start_utc = start_time.astimezone(pytz.UTC)

        return now_utc >= start_utc

class Candidate(models.Model):
    """
    Represents a candidate in a voting.

    Candidates can be associated with a specific voting and post, and can receive votes from voters.
    They can have a name, description, and optional photo.
    Candidates can be created without assigning to a voting, and assigned later.
    """
    voting = models.ForeignKey(Voting, on_delete=models.CASCADE, related_name='candidates', blank=True, null=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='candidates', blank=True, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='candidate_photos/', blank=True, null=True)

    def __str__(self):
        if self.voting and self.post:
            return f"{self.name} - {self.post.title} - {self.voting.title}"
        elif self.voting:
            return f"{self.name} - {self.voting.title} (No post assigned)"
        return f"{self.name} - (No voting or post assigned)"

    def vote_count(self):
        """
        Count the number of votes this candidate has received.

        Returns:
            int: The number of votes
        """
        return self.votes.count()

    @property
    def photo_url(self):
        """
        Get the URL of the candidate's photo or a default image if none exists.

        Returns:
            str: URL to the candidate's photo or default image
        """
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url
        return '/static/images/default-candidate.png'

    def save(self, *args, **kwargs):
        """
        Override save method to handle photo replacement.

        When a candidate's photo is updated, this method ensures that
        the old photo file is deleted from storage to prevent orphaned files.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        # Check if this is an existing candidate being updated
        if self.pk:
            try:
                # Get the old instance from the database
                old_instance = Candidate.objects.get(pk=self.pk)
                # If the photo has changed and there was an old photo, delete the old one
                if old_instance.photo and self.photo != old_instance.photo:
                    storage = old_instance.photo.storage
                    file_name = old_instance.photo.name
                    if storage.exists(file_name):
                        storage.delete(file_name)
            except Candidate.DoesNotExist:
                pass  # This is a new instance, so no old photo to delete
        # Call the parent save method
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete method to also remove the candidate's photo file.

        When a candidate is deleted, this method ensures that any associated
        photo file is also deleted from storage to prevent orphaned files.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        # Delete the image file if it exists
        if self.photo:
            # Get the storage system
            storage = self.photo.storage
            # Get the file name
            file_name = self.photo.name
            # Delete the file if it exists
            if storage.exists(file_name):
                storage.delete(file_name)
        # Call the parent delete method
        super().delete(*args, **kwargs)

class VotingVoter(models.Model):
    """
    Represents the assignment of a voter to a voting.

    This is a many-to-many relationship between votings and voters,
    indicating which voters are eligible to participate in which votings.
    """
    voting = models.ForeignKey(Voting, on_delete=models.CASCADE, related_name='voting_voters')
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voting_assignments')

    class Meta:
        unique_together = ('voting', 'voter')

    def __str__(self):
        return f"{self.voter.username} - {self.voting.title}"

class Vote(models.Model):
    """
    Represents a vote cast by a voter for a candidate in a voting.

    Each voter can vote for one candidate per post in each voting. The vote records
    which candidate was selected for which post and when the vote was cast.
    """
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    voting = models.ForeignKey(Voting, on_delete=models.CASCADE, related_name='votes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # This will ensure a voter can only vote once for each post in a voting
        # If post is null, it will be treated as a separate unique value
        unique_together = ('voter', 'voting', 'post')

    def __str__(self):
        if self.post:
            return f"{self.voter.username} voted for {self.candidate.name} for {self.post.title} in {self.voting.title}"
        else:
            return f"{self.voter.username} voted for {self.candidate.name} in {self.voting.title}"
