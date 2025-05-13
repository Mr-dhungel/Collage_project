"""
Script to update the ALLOWED_HOSTS setting in the Django settings.py file.
This script is meant to be run during the Railway deployment process.
"""

import os
import sys

def update_allowed_hosts():
    """Update the ALLOWED_HOSTS setting in the Django settings.py file."""
    # Get the Railway domain from the environment
    railway_domain = os.environ.get('RAILWAY_STATIC_URL', '')
    if railway_domain:
        # Extract the domain from the URL
        if '//' in railway_domain:
            railway_domain = railway_domain.split('//')[1]
        if '/' in railway_domain:
            railway_domain = railway_domain.split('/')[0]
        
        print(f"Detected Railway domain: {railway_domain}")
        
        # Add the domain to ALLOWED_HOSTS
        allowed_hosts = os.environ.get('ALLOWED_HOSTS', '')
        if railway_domain not in allowed_hosts:
            if allowed_hosts:
                allowed_hosts = f"{railway_domain},{allowed_hosts}"
            else:
                allowed_hosts = railway_domain
            
            # Set the environment variable
            os.environ['ALLOWED_HOSTS'] = allowed_hosts
            print(f"Updated ALLOWED_HOSTS: {allowed_hosts}")
        else:
            print(f"Railway domain already in ALLOWED_HOSTS: {allowed_hosts}")
    else:
        print("No Railway domain detected.")

if __name__ == '__main__':
    update_allowed_hosts()
