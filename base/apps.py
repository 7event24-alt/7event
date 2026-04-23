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
                firebase_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
                if firebase_creds:
                    from firebase_admin import credentials
                    import json
                    cred = credentials.Certificate(json.loads(firebase_creds))
                    firebase_admin.initialize_app(cred)
                    logging.info('Firebase initialized from env')
                else:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    cred_file = os.path.join(base_dir, 'event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json')
                    if os.path.exists(cred_file):
                        from firebase_admin import credentials
                        cred = credentials.Certificate(cred_file)
                        firebase_admin.initialize_app(cred)
                        logging.info('Firebase initialized from file')
                    else:
                        logging.warning('Firebase credentials not found')
        except Exception as e:
            logging.warning(f'Firebase initialization failed: {e}')
