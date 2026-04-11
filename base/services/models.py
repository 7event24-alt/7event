from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Service(models.Model):
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("Conta"),
    )
    name = models.CharField(max_length=200, verbose_name=_("Nome do Serviço"))
    description = models.TextField(blank=True, verbose_name=_("Descrição"))

    estimated_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Duração Estimada (horas)"),
    )
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Valor da Hora (R$)")
    )
    typical_expenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Despesas Típicas (R$)"),
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Ativo"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "services"
        verbose_name = _("Serviço")
        verbose_name_plural = _("Serviços")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def estimated_total(self):
        return (
            self.hourly_rate * self.estimated_duration_hours
        ) + self.typical_expenses
