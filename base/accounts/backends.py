from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import re

User = get_user_model()


class AuthenticationError(Exception):
    pass


def normalize_phone(phone):
    if not phone:
        return None
    return re.sub(r"\D", "", phone)


class PhoneEmailUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        phone_normalized = normalize_phone(username)

        query = Q(username__iexact=username) | Q(email__iexact=username)
        if phone_normalized:
            users_with_phone = User.objects.filter(
                phone__isnull=False
            ).exclude(phone="")
            for user in users_with_phone:
                if normalize_phone(user.phone) == phone_normalized:
                    query |= Q(pk=user.pk)
                    break

        try:
            user = User.objects.get(query)
        except User.DoesNotExist:
            return None

        if not user.is_active:
            return None

        if user.check_password(password):
            return user
        return None

    def authenticate_with_message(
        self, request, username=None, password=None, **kwargs
    ):
        if username is None or password is None:
            return None, "Preencha usuário e senha."

        phone_normalized = normalize_phone(username)

        query = Q(username__iexact=username) | Q(email__iexact=username)
        if phone_normalized:
            users_with_phone = User.objects.filter(
                phone__isnull=False
            ).exclude(phone="")
            for user in users_with_phone:
                if normalize_phone(user.phone) == phone_normalized:
                    query |= Q(pk=user.pk)
                    break

        try:
            user = User.objects.get(query)
        except User.DoesNotExist:
            return None, "Usuário não encontrado."

        if not user.is_active:
            return None, "Sua conta está inativa. Entre em contato com o suporte."

        if user.check_password(password):
            return user, None
        return None, "Senha incorreta."