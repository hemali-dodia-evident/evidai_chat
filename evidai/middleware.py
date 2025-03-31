from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.db import connections
import os
import logging

# Configure the logging settings
logger = logging.getLogger(__name__)

class DatabaseSelectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Switch database based on request headers, but only if needed."""
        try:
            env = request.headers.get('X-Environment', 'uat').lower()  # Default to UAT
            logger.info(f"Received request for environment: {env}")

            # Determine which DB settings to use
            if 'prod' in env:
                new_db_settings = {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': os.getenv('DB_NAME', ''),
                    'USER': os.getenv('DB_USER', ''),
                    'PASSWORD': os.getenv('DB_PASS', ''),
                    'HOST': os.getenv('DB_HOST', ''),
                    'PORT': os.getenv('DB_PORT', ''),
                    'ATOMIC_REQUESTS': True, 
                    'AUTOCOMMIT': True,
                    'TIME_ZONE': 'UTC',
                    'CONN_HEALTH_CHECKS': True,
                    'CONN_MAX_AGE': 60,
                    'OPTIONS': {},
                }
                new_url = os.getenv('URL', '')
                logger.info(f"Switching to PROD DB: {new_db_settings['NAME']} at {new_db_settings['HOST']}")
            else:
                new_db_settings = {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': os.getenv('UAT_DB_NAME', ''),
                    'USER': os.getenv('UAT_DB_USER', ''),
                    'PASSWORD': os.getenv('UAT_DB_PASS', ''),
                    'HOST': os.getenv('UAT_DB_HOST', ''),
                    'PORT': os.getenv('UAT_DB_PORT', ''),
                    'ATOMIC_REQUESTS': True, 
                    'TIME_ZONE': 'UTC',
                    'CONN_HEALTH_CHECKS': True,
                    'CONN_MAX_AGE': 60,
                    'OPTIONS': {},
                }
                new_url = os.getenv('UAT_URL', '')
                logger.info(f"Switching to UAT DB: {new_db_settings['NAME']} at {new_db_settings['HOST']}")

            # Check if database settings need an update
            if settings.DATABASES.get('default') != new_db_settings:
                logger.info(f"Updating database settings for: {env}")

                # Close existing connections before switching
                for conn in connections.all():
                    conn.close()

                # Update settings
                settings.DATABASES['default'] = new_db_settings
                settings.URL = new_url
            else:
                logger.info(f"Database settings for {env} are already set. Skipping update.")

        except Exception as e:
            logger.error(f"Error in DatabaseSelectionMiddleware: {e}")

            # Fallback to UAT settings in case of failure
            settings.DATABASES['default'] = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('UAT_DB_NAME', ''),
                'USER': os.getenv('UAT_DB_USER', ''),
                'PASSWORD': os.getenv('UAT_DB_PASS', ''),
                'HOST': os.getenv('UAT_DB_HOST', ''),
                'PORT': os.getenv('UAT_DB_PORT', ''),
                'ATOMIC_REQUESTS': True, 
                'TIME_ZONE': 'UTC',
                'CONN_HEALTH_CHECKS': True,
                'CONN_MAX_AGE': 60,
                'OPTIONS': {},
            }
            settings.URL = os.getenv('UAT_URL', '')

            logger.info(f"Falling back to UAT DB: {settings.DATABASES['default']['NAME']} at {settings.DATABASES['default']['HOST']}")
