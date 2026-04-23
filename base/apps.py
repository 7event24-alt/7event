from django.apps import AppConfig
import logging
import os

logger = logging.getLogger(__name__)

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
            logger.info('Firebase already initialized')
            return
        
        try:
            # Try environment variable first
            firebase_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
            if firebase_creds:
                import json
                cred = credentials.Certificate(json.loads(firebase_creds))
                firebase_admin.initialize_app(cred)
                logger.info('Firebase initialized from env')
                return
            
            # Try direct path
            cred_file = '/var/www/7event/event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json'
            
            if os.path.exists(cred_file):
                cred = credentials.Certificate(cred_file)
                firebase_admin.initialize_app(cred)
                logger.info(f'Firebase initialized from {cred_file}')
                return
            
            logger.warning(f'Firebase credentials not found at {cred_file}')
        except Exception as e:
            logger.warning(f'Firebase initialization failed: {e}')
