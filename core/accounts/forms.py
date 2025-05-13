from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class UserIdForm(forms.Form):
    user_id = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Username or Voter ID'})
    )

class PasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')
        else:
            self.user = None
        super().__init__(*args, **kwargs)

class VoterCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    enable_facial_recognition = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Enable facial recognition for this voter"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'middle_name', 'last_name', 'gender', 'password1', 'password2', 'enable_facial_recognition']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_voter = True
        user.is_admin = False
        if commit:
            user.save()
        return user


class AdminCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    # Admin permissions
    can_manage_voters = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Allow this admin to manage voters (add, edit, delete)"
    )
    can_manage_votings = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Allow this admin to manage votings (add, edit, delete)"
    )
    can_manage_candidates = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Allow this admin to manage candidates (add, edit, delete)"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2',
                 'can_manage_voters', 'can_manage_votings', 'can_manage_candidates']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_admin = True
        user.is_voter = False
        user.voter_id = None
        user.is_staff = True  # Needed for Django admin access
        if commit:
            user.save()
        return user


class AdminUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username',
                 'can_manage_voters', 'can_manage_votings', 'can_manage_candidates']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'can_manage_voters': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_votings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_candidates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class VoterUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'middle_name', 'last_name', 'gender', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
