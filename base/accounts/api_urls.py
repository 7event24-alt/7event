from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_auth
import json
import os

router = DefaultRouter()
router.register(r"auth", api_auth.AuthViewSet, basename="auth-api")
router.register(r"users", api_auth.AuthViewSet, basename="users-api")

VAPID_PUBLIC_KEY = 'BKyYU7KuJKgqgkv2I9zMKvO86H9nbXWluSaPXjjxa02i9TkD9z2gcMypUiyCUrmZEi4weSQSK4MfE97TlzFkQyM'
VAPID_PRIVATE_KEY = 'kb_zvHKqPQVSJrCwCVh7aPrrKNPPHHv3Cj1DNcUGrCk'

def send_web_push(subscription, title, body):
    """Send web push notification using pywebpush"""
    import pywebpush
    
    if not VAPID_PRIVATE_KEY:
        import logging
        logging.getLogger(__name__).error("VAPID_PRIVATE_KEY not configured")
        return False
    
    try:
        subscription_dict = json.loads(subscription) if isinstance(subscription, str) else subscription
        
        pywebpush.webpush(
            subscription_dict,
            json.dumps({
                'title': title,
                'body': body
            }),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={'sub': 'mailto:admin@7event.com.br'}
        )
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Web push error: {e}")
        return False

# View para salvar token FCM
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def save_fcm_token(request):
    if request.method == 'POST':
        try:
            from .models import FCMToken
            from rest_framework.response import Response
            
            token = request.data.get('token')
            device_type = request.data.get('device_type', 'web')
            
            user = request.user if request.user.is_authenticated else None
            
            if token and user:
                FCMToken.objects.update_or_create(
                    user=user,
                    device_type=device_type,
                    defaults={
                        'token': token,
                        'is_active': True
                    }
                )
                return Response({'message': 'Notificação configurada! Você receberá push notifications.'})
            elif token:
                return Response({'message': 'Token salvo (anon)'})
            else:
                return Response({'error': 'Token não fornecido'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    return Response({'error': 'Method not allowed'}, status=405)

APP_NAME = "7event"

def send_push_notification(user, title, body, action_url=None):
    """Helper function to send push notification to a user"""
    from .models import FCMToken
    import firebase_admin
    from firebase_admin import messaging
    
    if not firebase_admin._apps:
        return False
    
    try:
        tokens = FCMToken.objects.filter(user=user, is_active=True)
        if not tokens.exists():
            return False
        
        full_title = f"{APP_NAME} - {title}"
        
        for fcm_token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=full_title,
                        body=body
                    ),
                    token=fcm_token.token,
                    data={
                        'title': full_title,
                        'body': body,
                        'url': action_url or '/'
                    }
                )
                messaging.send(message)
            except Exception:
                pass
        
        return True
    except Exception:
        return False

# View para enviar notificação FCM via Firebase Admin SDK
def send_fcm_notification(request):
    from rest_framework.response import Response
    from rest_framework import status
    from .models import FCMToken
    import firebase_admin
    from firebase_admin import messaging
    
    if not firebase_admin._apps:
        import logging
        logging.getLogger(__name__).error("Firebase not initialized")
        return Response({'error': 'Firebase not configured'}, status=500)
    
    if request.method == 'POST':
        try:
            title = request.data.get('title', 'Notificação')
            body = request.data.get('body', '')
            
            full_title = f"{APP_NAME} - {title}"
            
            if request.user.is_staff:
                tokens = FCMToken.objects.filter(is_active=True)
            elif request.user.is_authenticated:
                tokens = FCMToken.objects.filter(user=request.user, is_active=True)
            else:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            if not tokens.exists():
                return Response({'error': 'Nenhum token cadastrado'}, status=status.HTTP_400_BAD_REQUEST)
            
            sent_count = 0
            for fcm_token in tokens:
                try:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=full_title,
                            body=body
                        ),
                        token=fcm_token.token,
                        data={
                            'title': full_title,
                            'body': body,
                            'url': '/'
                        }
                    )
                    messaging.send(message)
                    sent_count += 1
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f'FCM send error: {e}')
            
            return Response({
                'status': 'sent',
                'recipients': sent_count,
                'title': title,
                'body': body
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def send_fcm_test(request):
    from rest_framework.response import Response
    from rest_framework import status
    import json
    from django.conf import settings
    
    try:
        if request.method == 'GET':
            return Response({'status': 'ok', 'message': 'FCM test endpoint'})
        
        # Bypass auth
        
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        subscription_data = request.data.get('subscription')
        
        # Convert to JSON string if it's a dict
        if isinstance(subscription_data, dict):
            subscription_data = json.dumps(subscription_data)
        
        logger.error(f"Push: subscription type: {type(subscription_data)}")
        
        if not subscription_data:
            return Response({'error': 'Subscription requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        filename = '/tmp/push_subscriptions.txt'
        with open(filename, 'a') as f:
            f.write(subscription_data + '\n')
        
        logger.error(f"Push: Written to {filename}")
        
        return Response({
            'status': 'success',
            'message': 'Subscription registrada!',
            'subscription_recebido': True
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("fcm/token/", save_fcm_token, name="fcm_save_token"),
    path("fcm/send/", send_fcm_notification, name="fcm_send"),
    path("fcm/test/", send_fcm_test, name="fcm_test"),
]