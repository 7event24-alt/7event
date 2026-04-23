from django.apps import AppConfig
import logging
import os


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
            logging.info('Firebase already initialized')
            return
        
        try:
            # Try environment variable first
            firebase_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
            if firebase_creds:
                import json
                cred = credentials.Certificate(json.loads(firebase_creds))
                firebase_admin.initialize_app(cred)
                logging.info('Firebase initialized from env')
                return
            
            # Direct paths to try
            possible_paths = [
                '/var/www/7event/event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json',
                '/home/bia/Projetos_Pessoais/7event/event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json',
                os.path.join(os.getcwd(), 'event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json'),
            ]
            
            for cred_file in possible_paths:
                if os.path.exists(cred_file):
                    logging.info(f'Found credentials at: {cred_file}')
                    cred = credentials.Certificate(cred_file)
                    firebase_admin.initialize_app(cred)
                    logging.info(f'Firebase initialized from {cred_file}')
                    return
            
            logging.warning('Firebase credentials not found')
        except Exception as e:
            logging.warning(f'Firebase initialization failed: {e}')
