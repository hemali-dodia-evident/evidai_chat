from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import os
import logging

# Configure the logging settings
logger = logging.getLogger(__name__)

class DatabaseSelectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Switch database based on request headers, but only if needed"""
        try:
            host = request.headers.get('X-Environment', '').lower()
            logger.info(f"Received request for environment: {host}")

            if 'prod' in host:
                new_db_settings = {
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
                    'CONN_MAX_AGE': 60,
                    'OPTIONS': {},
                }
                new_url = os.getenv('URL')
                logger.info(f"DB Connection Details - \nDB Name - {os.getenv('DB_NAME')}\nHost - {os.getenv('DB_HOST')}")
            
            else:
                new_db_settings = {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': os.getenv('UAT_DB_NAME'),
                    'USER': os.getenv('UAT_DB_USER'),
                    'PASSWORD': os.getenv('UAT_DB_PASS'),
                    'HOST': os.getenv('UAT_DB_HOST'),
                    'PORT': os.getenv('UAT_DB_PORT'),
                    'ATOMIC_REQUESTS': True, 
                    'TIME_ZONE': 'UTC',
                    'CONN_HEALTH_CHECKS': True,
                    'CONN_MAX_AGE': 60,
                    'OPTIONS': {},
                }
                new_url = os.getenv('UAT_URL')

            # Check if database settings need an update
            if settings.DATABASES.get('default') != new_db_settings:
                logger.info(f"Updating database settings for: {host}")
                logger.info(f"DB Connection Details - \nDB Name - {os.getenv('UAT_DB_NAME')}\nHost - {os.getenv('UAT_DB_HOST')}")
            
                settings.DATABASES['default'] = new_db_settings
                settings.URL = new_url
            else:
                logger.info(f"Database settings for {host} are already set. Skipping update.")

        except Exception as e:
            logger.error(f"Error in DatabaseSelectionMiddleware: {e}")
            logger.info(f"DB Connection Details - \nDB Name - {os.getenv('UAT_DB_NAME')}\nHost - {os.getenv('UAT_DB_HOST')}")
            # Use UAT settings as fallback
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
                'CONN_MAX_AGE': 60,
                'OPTIONS': {},
            }
            settings.URL = os.getenv('UAT_URL')
