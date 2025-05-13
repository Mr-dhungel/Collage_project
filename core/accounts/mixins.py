from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires the user to be an admin.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('home')

class VoterRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires the user to be a voter.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_voter

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('home')
