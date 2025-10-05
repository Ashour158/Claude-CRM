# config/wsgi.py
# WSGI configuration for Django application

import os
from django.core.wsgi import get_wsgi_application

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get WSGI application
application = get_wsgi_application()