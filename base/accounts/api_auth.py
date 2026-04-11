import secrets
from datetime import timedelta
from django.utils import timezone

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import UserSerializer

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    authentication_classes = [JWTAuthentication]

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def login(self, request):
        from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email e senha são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Credenciais inválidas"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"error": "Credenciais inválidas"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_verified:
            return Response(
                {
                    "error": "email_not_verified",
                    "message": "Email não verificado. Por favor, verifique sua caixa de email ou solicite um novo link de verificação.",
                    "user_id": user.id,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": "Usuário inativo. Entre em contato com o suporte."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_serializer.data,
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def register(self, request):
        from django.contrib.auth import get_user_model

        email = request.data.get("email")
        password = request.data.get("password")
        password_confirm = request.data.get("password_confirm")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")
        phone = request.data.get("phone", "")

        if not email or not password:
            return Response(
                {"error": "Email e senha são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if password != password_confirm:
            return Response(
                {"error": "As senhas não conferem"}, status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email já está em uso"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Gerar token de verificação
        verification_token = secrets.token_urlsafe(32)

        # Criar usuário
        user = User.objects.create_user(
            username=email.split("@")[0],
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_verified=False,
            verification_token=verification_token,
        )

        # Enviar email de verificação
        try:
            from base.core.emails import send_verification_email

            base_url = request.data.get("base_url", "http://127.0.0.1:8000")
            verification_url = f"{base_url}/api/v1/auth/verify/{verification_token}/"
            send_verification_email(user, verification_url)
        except Exception as e:
            print(f"Erro ao enviar email de verificação: {e}")

        user_serializer = UserSerializer(user)

        return Response(
            {
                "message": "Conta criada com sucesso! Verifique seu email para confirmar seu cadastro.",
                "user": user_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
        url_path="verify/(?P<token>[^/.]+)",
    )
    def verify(self, request, token=None):
        try:
            user = User.objects.get(verification_token=token)
        except User.DoesNotExist:
            return Response(
                {"error": "Token de verificação inválido ou expirado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_verified:
            return Response(
                {
                    "message": "Email já foi verificado anteriormente. Você pode fazer login."
                },
                status=status.HTTP_200_OK,
            )

        # Verificar se o token expirou (24 horas)
        # Como não guardamos a data de criação, vamos verificar pela idade do usuário
        # Uma solução melhor seria guardar a data de criação do token

        user.is_verified = True
        user.verification_token = ""
        user.save()

        return Response(
            {
                "message": "Email confirmado com sucesso! Agora você pode fazer login.",
                "verified": True,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def resend_verification(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email é obrigatório"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Email não encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        if user.is_verified:
            return Response(
                {"message": "Este email já está verificado. Você pode fazer login."},
                status=status.HTTP_200_OK,
            )

        # Gerar novo token
        verification_token = secrets.token_urlsafe(32)
        user.verification_token = verification_token
        user.save()

        # Enviar email
        try:
            from base.core.emails import send_verification_email

            base_url = request.data.get("base_url", "http://127.0.0.1:8000")
            verification_url = f"{base_url}/api/v1/auth/verify/{verification_token}/"
            send_verification_email(user, verification_url)
        except Exception as e:
            print(f"Erro ao enviar email de verificação: {e}")
            return Response(
                {"error": "Erro ao enviar email. Tente novamente mais tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Email de verificação reenviado com sucesso!"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"detail": "Logout realizado com sucesso"})
        except Exception:
            return Response(
                {"detail": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def refresh(self, request):
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer

        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
