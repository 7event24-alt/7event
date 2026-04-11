from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ExpenseCategory(models.TextChoices):
    EQUIPMENT = "equipment", _("Equipamento")
    TRANSPORT = "transport", _("Transporte")
    FOOD = "food", _("Alimentação")
    ACCOMMODATION = "accommodation", _("Hospedagem")
    MARKETING = "marketing", _("Marketing")
    FEE = "fee", _("Taxa/Imposto")
    OTHER = "other", _("Outro")


class Expense(models.Model):
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name=_("Conta"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="expenses_created",
        verbose_name=_("Criado por"),
        null=True,
        blank=True,
    )
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name=_("Trabalho"),
    )

    category = models.CharField(
        max_length=20,
        choices=ExpenseCategory.choices,
        default=ExpenseCategory.OTHER,
        verbose_name=_("Categoria"),
    )
    value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Valor")
    )
    date = models.DateField(verbose_name=_("Data"))
    description = models.TextField(blank=True, verbose_name=_("Descrição"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expenses"
        verbose_name = _("Despesa")
        verbose_name_plural = _("Despesas")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.category} - R$ {self.value}"
