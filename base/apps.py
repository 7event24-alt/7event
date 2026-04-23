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
        try:
            import firebase_admin
            
            if not firebase_admin._apps:
                from firebase_admin import credentials
                
                # Try environment variable first
                firebase_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
                if firebase_creds:
                    import json
                    cred = credentials.Certificate(json.loads(firebase_creds))
                    firebase_admin.initialize_app(cred)
                    logging.info('Firebase initialized from env')
                else:
                    # Try multiple paths
                    base_paths = [
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        '/var/www/7event',
                        '/home/bia/Projetos_Pessoais/7event'
                    ]
                    
                    cred_file = None
                    for base in base_paths:
                        fpath = os.path.join(base, 'event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json')
                        if os.path.exists(fpath):
                            cred_file = fpath
                            break
                    
                    if cred_file:
                        cred = credentials.Certificate(cred_file)
                        firebase_admin.initialize_app(cred)
                        logging.info(f'Firebase initialized from {cred_file}')
                    else:
                        logging.warning('Firebase credentials not found')
        except Exception as e:
            logging.warning(f'Firebase initialization failed: {e}')
