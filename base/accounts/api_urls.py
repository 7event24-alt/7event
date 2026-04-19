from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_auth
import json
import os

router = DefaultRouter()
router.register(r"auth", api_auth.AuthViewSet, basename="auth-api")
router.register(r"users", api_auth.AuthViewSet, basename="users-api")

# View para salvar token FCM
def save_fcm_token(request):
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import AllowAny
    from rest_framework.response import Response
    from rest_framework import status
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')
            
            if token:
                from django.conf import settings
                
                filename = os.path.join(settings.BASE_DIR, 'base', 'static', 'fcm_tokens.txt')
                with open(filename, 'a') as f:
                    f.write(f"{token}\n")
                
                return Response({'status': 'saved'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# View para enviar notificação FCM (admin)
def send_fcm_notification(request):
    from rest_framework.permissions import IsAdminUser
    from rest_framework.response import Response
    from rest_framework import status
    
    if request.method == 'POST':
        try:
            if not request.user.is_staff:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            data = json.loads(request.body)
            title = data.get('title', '7event')
            body = data.get('body', '')
            
            from django.conf import settings
            filename = os.path.join(settings.BASE_DIR, 'base', 'static', 'fcm_tokens.txt')
            
            tokens = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    tokens = [line.strip() for line in f if line.strip()]
            
            if not tokens:
                return Response({'error': 'Nenhum token cadastrado'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'status': 'sent',
                'recipients': len(tokens),
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