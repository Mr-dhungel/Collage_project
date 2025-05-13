"""
Custom middleware for the Voting System project.
"""

from django.conf import settings
import os

class DynamicAllowedHostsMiddleware:
    """
    Middleware to dynamically add the current host to ALLOWED_HOSTS.
    This is useful for Railway deployments where the domain might change.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get the current host
        host = request.get_host()
        
        # Check if the host is already in ALLOWED_HOSTS
        if host not in settings.ALLOWED_HOSTS:
            # Add the host to ALLOWED_HOSTS
            settings.ALLOWED_HOSTS.append(host)
            print(f"Added {host} to ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        # Call the next middleware/view
        response = self.get_response(request)
        return response
