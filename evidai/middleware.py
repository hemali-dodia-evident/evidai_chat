from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import os

class DatabaseSelectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Switch database based on request headers"""
        if request.headers.get('X-Environment') == 'prod':
            settings.DATABASES['default'] = {
                        'ENGINE': 'django.db.backends.postgresql',
                        'NAME': os.getenv('DB_NAME'),
                        'USER': os.getenv('DB_USER'),
                        'PASSWORD': os.getenv('DB_PASS'),
                        'HOST': os.getenv('DB_HOST'),
                        'PORT': os.getenv('DB_PORT'),
                        'ATOMIC_REQUESTS': True, 
                        'AUTOCOMMIT': True,
                        'TIME_ZONE': 'UTC',
                        'CONN_HEALTH_CHECKS': True,
                        'CONN_MAX_AGE': 60,  # Keeps database connections open for reuse (in seconds)
                        'OPTIONS': {},  # Additional database options (optional, can be empty)
                    }
        else:
            settings.DATABASES['default'] = {
                        'ENGINE': 'django.db.backends.postgresql',
                        'NAME': os.getenv('UAT_DB_NAME'),
                        'USER': os.getenv('UAT_DB_USER'),
                        'PASSWORD': os.getenv('UAT_DB_PASS'),
                        'HOST': os.getenv('UAT_DB_HOST'),
                        'PORT': os.getenv('UAT_DB_PORT'),
                        'ATOMIC_REQUESTS': True, 
                        'TIME_ZONE': 'UTC',
                        'CONN_HEALTH_CHECKS': True,
                        'CONN_MAX_AGE': 60,  # Keeps database connections open for reuse (in seconds)
                        'OPTIONS': {},  # Additional database options (optional, can be empty)
                    }
            