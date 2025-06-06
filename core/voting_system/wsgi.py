"""
WSGI config for voting_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from voting_system.media_setup import ensure_media_dirs

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voting_system.settings')

# Ensure media directories exist on startup
ensure_media_dirs()

application = get_wsgi_application()
