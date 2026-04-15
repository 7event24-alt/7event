from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="clients",
        verbose_name=_("Conta"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="clients_created",
        verbose_name=_("Criado por"),
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200, verbose_name=_("Nome"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(
        max_length=20, verbose_name=_("Telefone"), blank=False, default=""
    )
    document = models.CharField(max_length=18, blank=True, verbose_name=_("CPF/CNPJ"))
    address = models.TextField(blank=True, verbose_name=_("Endereço"))
    notes = models.TextField(blank=True, verbose_name=_("Observações"))
    is_active = models.BooleanField(default=True, verbose_name=_("Ativo"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients"
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def jobs_count(self):
        return self.jobs.count()

    @property
    def total_revenue(self):
        return sum(job.cache or 0 for job in self.jobs.all())
