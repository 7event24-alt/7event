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
            
            # Direct paths to try
            possible_paths = [
                '/var/www/7event/event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json',
                '/home/bia/Projetos_Pessoais/7event/event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json',
            ]
            
            logger.info(f'Paths to check: {possible_paths}')
            logger.info(f'Current dir: {os.getcwd()}')
            
            for cred_file in possible_paths:
                exists = os.path.exists(cred_file)
                logger.info(f'Path {cred_file}: exists={exists}')
                if exists:
                    cred = credentials.Certificate(cred_file)
                    firebase_admin.initialize_app(cred)
                    logger.info(f'Firebase initialized from {cred_file}')
                    return
            
            logger.warning('Firebase credentials not found')
        except Exception as e:
            logger.warning(f'Firebase initialization failed: {e}')
