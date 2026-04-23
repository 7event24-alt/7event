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
            
            # Try to find the credentials file
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cred_filename = 'event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json'
            cred_file = os.path.join(project_root, cred_filename)
            
            logger.info(f'Project root: {project_root}')
            logger.info(f'Checking: {cred_file}')
            
            if os.path.exists(cred_file):
                cred = credentials.Certificate(cred_file)
                firebase_admin.initialize_app(cred)
                logger.info(f'Firebase initialized from {cred_file}')
                return
            
            # Check parent directory (if running from venv)
            parent_root = os.path.dirname(project_root)
            cred_file2 = os.path.join(parent_root, cred_filename)
            logger.info(f'Checking parent: {cred_file2}')
            
            if os.path.exists(cred_file2):
                cred = credentials.Certificate(cred_file2)
                firebase_admin.initialize_app(cred)
                logger.info(f'Firebase initialized from {cred_file2}')
                return
            
            logger.warning(f'Firebase credentials not found in {project_root} or {parent_root}')
        except Exception as e:
            logger.warning(f'Firebase initialization failed: {e}')
