from django.apps import AppConfig
import logging


class BaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base"
    verbose_name = "Base"
    
    def ready(self):
        self.initialize_firebase()
    
    def initialize_firebase(self):
        try:
            import firebase_admin
            from firebase_admin import credentials
            
            if not firebase_admin._apps:
                import os
                import json
                
                # Try environment variable first
                firebase_creds = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
                if firebase_creds:
                    cred = credentials.Certificate(json.loads(firebase_creds))
                    firebase_admin.initialize_app(cred)
                    logging.info('Firebase initialized from env')
                else:
                    # Try to load from file
                    import os
                    from django.conf import settings
                    cred_file = os.path.join(settings.BASE_DIR, 'firebase-creds.json')
                    if os.path.exists(cred_file):
                        cred = credentials.Certificate(cred_file)
                        firebase_admin.initialize_app(cred)
                        logging.info('Firebase initialized from file')
                    else:
                        logging.warning('Firebase credentials not found')
        except Exception as e:
            logging.warning(f'Firebase initialization failed: {e}')
