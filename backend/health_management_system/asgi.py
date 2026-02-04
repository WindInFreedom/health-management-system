"""
ASGI config for health_management_system project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')

application = get_asgi_application()
