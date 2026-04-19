from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import re

User = get_user_model()


class AuthenticationError(Exception):
    """Exceção customizada para erros de autenticação"""

    pass


def normalize_phone(phone):
    """Normaliza telefone para comparação - remove máscara"""
    if not phone:
        return None
    return re.sub(r"\D", "", phone)


class PhoneEmailUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Normalizar telefone se for um número de telefone
        phone_normalized = normalize_phone(username)

        # Buscar por username, email ou telefone normalizado
        query = Q(username__iexact=username) | Q(email__iexact=username)
        if phone_normalized:
            # Buscar usuários com telefone e comparar normalizado
            users_with_phone = (
                User.objects.select_related("account")
                .filter(phone__isnull=False)
                .exclude(phone="")
            )
            for user in users_with_phone:
                if normalize_phone(user.phone) == phone_normalized:
                    query |= Q(pk=user.pk)
                    break

        try:
            user = User.objects.select_related("account").get(query)
        except User.DoesNotExist:
            return None

        if not user.is_active:
            return None

        if user.account and user.account.is_blocked:
            return None

        if user.check_password(password):
            return user
        return None

    def authenticate_with_message(
        self, request, username=None, password=None, **kwargs
    ):
        """Versão do authenticate que retorna mensagem de erro customizada"""
        if username is None or password is None:
            return None, "Preencha usuário e senha."

        phone_normalized = normalize_phone(username)

        query = Q(username__iexact=username) | Q(email__iexact=username)
        if phone_normalized:
            users_with_phone = (
                User.objects.select_related("account")
                .filter(phone__isnull=False)
                .exclude(phone="")
            )
            for user in users_with_phone:
                if normalize_phone(user.phone) == phone_normalized:
                    query |= Q(pk=user.pk)
                    break

        try:
            user = User.objects.select_related("account").get(query)
        except User.DoesNotExist:
            return None, "Usuário não encontrado."

        if not user.is_active:
            return None, "Sua conta está inativa. Entre em contato com o suporte."

        if user.account and user.account.is_blocked:
            return None, "Sua conta está bloqueada. Entre em contato com o suporte."

        if user.check_password(password):
            return user, None
        return None, "Senha incorreta."
