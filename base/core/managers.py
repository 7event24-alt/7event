from django.db import models


class OwnershipManager(models.Manager):
    """Manager que fornece métodos para filtragem por ownership do usuário."""

    def for_user(self, user):
        """Retorna querysets filtrados pelo usuário ou todos para superusers."""
        if user.is_superuser:
            return self.get_queryset()
        return self.get_queryset().filter(created_by=user)

    def active_for_user(self, user):
        """Retorna apenas ativos, filtrados pelo usuário."""
        return self.for_user(user).filter(is_active=True)


class ActiveManager(models.Manager):
    """Manager simples que retorna apenas itens ativos."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)