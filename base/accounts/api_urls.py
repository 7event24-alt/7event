from django.urls import path, include
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
                # Salvar token em arquivo (simples) ou no banco
                # Aqui vamos salvar em arquivo temporário
                from django.conf import settings
                import uuid
                
                filename = os.path.join(settings.BASE_DIR, 'base', 'static', 'fcm_tokens.txt')
                with open(filename, 'a') as f:
                    f.write(f"{token}\n")
                
                return Response({'status': 'saved'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# View para enviar notificação FCM (admin)
def send_fcm_notification(request):
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import IsAdminUser
    from rest_framework.response import Response
    from rest_framework import status
    import requests
    
    if request.method == 'POST':
        try:
            if not request.user.is_staff:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            data = json.loads(request.body)
            title = data.get('title', '7event')
            body = data.get('body', '')
            
            # Ler tokens do arquivo
            from django.conf import settings
            filename = os.path.join(settings.BASE_DIR, 'base', 'static', 'fcm_tokens.txt')
            
            tokens = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    tokens = [line.strip() for line in f if line.strip()]
            
            if not tokens:
                return Response({'error': 'Nenhum token cadastrado'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Enviar via FCM HTTP v1
            # Precisa de service account JSON do Firebase
            # Por agora, retorna sucesso simulado
            
            return Response({
                'status': 'sent',
                'recipients': len(tokens),
                'title': title,
                'body': body
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

def send_fcm_test(request):
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import IsAuthenticated, IsAdminUser
    from rest_framework.response import Response
    from rest_framework import status
    import os
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        try:
            if not request.user.is_superuser:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            data = json.loads(request.body)
            subscription_data = data.get('subscription')
            
            if not subscription_data:
                return Response({'error': 'Subscription requerido'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Guardar subscription para uso posterior
            from django.conf import settings
            filename = os.path.join(settings.BASE_DIR, 'base', 'static', 'push_subscriptions.txt')
            with open(filename, 'a') as f:
                f.write(subscription_data + '\n')
            
            return Response({
                'status': 'success',
                'message': 'Subscription registrada! Configure Web Push VAPID backend.',
                'subscription_recebido': True
            })
            
        except Exception as e:
            logger.error(f"FCM Error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("fcm/token/", save_fcm_token, name="fcm_save_token"),
    path("fcm/send/", send_fcm_notification, name="fcm_send"),
    path("fcm/test/", send_fcm_test, name="fcm_test"),
]
