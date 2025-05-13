from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import random

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        return self.create_user(username, password, **extra_fields)

class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say')
    ]

    is_admin = models.BooleanField(default=False)
    is_voter = models.BooleanField(default=True)
    voter_id = models.CharField(max_length=4, unique=True, blank=True, null=True)
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='N')
    has_face_data = models.BooleanField(default=False, help_text="Whether the user has facial recognition data registered")
    face_samples_count = models.PositiveSmallIntegerField(default=0, help_text="Number of face samples registered for this user")

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.voter_id and self.is_voter:
            # Generate a unique 4-digit voter ID
            while True:
                voter_id = str(random.randint(1000, 9999))
                if not User.objects.filter(voter_id=voter_id).exists():
                    self.voter_id = voter_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
