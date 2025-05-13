from django import forms
from django.utils import timezone
import pytz
from .models import Voting, Candidate, Vote, VotingVoter
from accounts.models import User

class VotingForm(forms.ModelForm):
    class Meta:
        model = Voting
        fields = ['title', 'description', 'start_time', 'end_time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            # Ensure both times are timezone-aware
            from django.utils import timezone
            import pytz

            # Helper function to ensure timezone awareness
            def ensure_timezone_aware(dt):
                if timezone.is_naive(dt):
                    # Make aware using the current timezone
                    return timezone.make_aware(dt)
                return dt

            # Make sure times are timezone-aware
            start_time = ensure_timezone_aware(start_time)
            end_time = ensure_timezone_aware(end_time)

            # Convert to UTC for storage
            start_time_utc = start_time.astimezone(pytz.UTC)
            end_time_utc = end_time.astimezone(pytz.UTC)

            cleaned_data['start_time'] = start_time_utc
            cleaned_data['end_time'] = end_time_utc

            # Validate that end time is after start time (compare in UTC)
            if end_time_utc <= start_time_utc:
                raise forms.ValidationError("End time must be after start time.")

        return cleaned_data

class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'description', 'photo', 'voting']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'voting': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        voting_pk = kwargs.pop('voting_pk', None)
        super().__init__(*args, **kwargs)

        # If we're creating a candidate for a specific voting
        if voting_pk:
            self.fields['voting'].initial = voting_pk
            self.fields['voting'].widget = forms.HiddenInput()
        else:
            # Only show active and upcoming votings in the dropdown
            from django.utils import timezone
            self.fields['voting'].queryset = Voting.objects.filter(
                end_time__gte=timezone.now()
            )

class VoteForm(forms.ModelForm):
    class Meta:
        model = Vote
        fields = ['candidate']
        widgets = {
            'candidate': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        voting = kwargs.pop('voting', None)
        super().__init__(*args, **kwargs)
        if voting:
            self.fields['candidate'].queryset = Candidate.objects.filter(voting=voting)

class VotingVoterForm(forms.ModelForm):
    voters = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_voter=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Voting
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['voters'].initial = User.objects.filter(
                voting_assignments__voting=self.instance
            )

    def save(self, commit=True):
        voting = super().save(commit=False)
        if commit:
            voting.save()

        if self.cleaned_data.get('voters'):
            # Remove all existing voters
            VotingVoter.objects.filter(voting=voting).delete()

            # Add selected voters
            for voter in self.cleaned_data['voters']:
                VotingVoter.objects.create(voting=voting, voter=voter)

        return voting
