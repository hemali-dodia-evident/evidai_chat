from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import os
import logging

# Configure the logging settings
logger = logging.getLogger(__name__)

class DatabaseSelectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Switch database based on request headers"""
        host = request.get_host()
        logging.info(f"{host}")
        if 'prod' in host:
            logging.info(f"Prod DB sesstings\n{os.getenv('DB_NAME')}\n")
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
            logging.info(f"Prod DB sesstings\n{os.getenv('UAT_DB_NAME')}\n")
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
            