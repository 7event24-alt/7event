from django.apps import AppConfig
import logging
import os

logger = logging.getLogger(__name__)

CRED_FILE = '/var/www/7event/event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json'

class BaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base"
    verbose_name = "Base"
    
    def ready(self):
        self.initialize_firebase()
    
    def initialize_firebase(self):
        import firebase_admin
        from firebase_admin import credentials
        
        if firebase_admin._apps:
            return
        
        try:
            if os.path.exists(CRED_FILE):
                cred = credentials.Certificate(CRED_FILE)
                firebase_admin.initialize_app(cred)
            else:
                logger.warning(f'Firebase creds not found at {CRED_FILE}')
        except Exception as e:
            logger.error(f'Firebase init failed: {e}')
