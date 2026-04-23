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
                'body': body,
                'icon': '/static/icons/icon-192.png'
            }),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={'subject': 'https://7event.com.br'}
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
            subscription = request.data.get('subscription')
            device_type = request.data.get('device_type', 'web')
            
            if subscription:
                from .models import FCMToken
                from rest_framework.response import Response
                
                keys = subscription.get('keys', {})
                p256dh = keys.get('p256dh', '')
                auth = keys.get('auth', '')
                
                user = request.user if request.user.is_authenticated else None
                
                if user:
                    FCMToken.objects.update_or_create(
                        user=user,
                        device_type=device_type,
                        defaults={
                            'token': p256dh,
                            'auth': auth,
                            'subscription': json.dumps(subscription)
                        }
                    )
                    return Response({'message': 'Notificação configurada! Você receberá push notifications.'})
                else:
                    return Response({'message': 'Notificação configurada (anon)'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    return Response({'error': 'Method not allowed'}, status=405)

# View para enviar notificação FCM (admin)
def send_fcm_notification(request):
    from rest_framework.permissions import IsAdminUser
    from rest_framework.response import Response
    from rest_framework import status
    from .models import FCMToken
    
    if request.method == 'POST':
        try:
            if not request.user.is_staff:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            title = request.data.get('title', '7event')
            body = request.data.get('body', '')
            
            # Buscar subscriptions da base de dados
            tokens = FCMToken.objects.filter(is_active=True)
            
            if not tokens.exists():
                return Response({'error': 'Nenhum token cadastrado'}, status=status.HTTP_400_BAD_REQUEST)
            
            sent_count = 0
            for fcm_token in tokens:
                try:
                    if fcm_token.subscription:
                        if send_web_push(fcm_token.subscription, title, body):
                            sent_count += 1
                except Exception as e:
                    pass
            
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