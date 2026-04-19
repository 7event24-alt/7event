from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class QuoteStatus(models.TextChoices):
    DRAFT = "draft", _("Rascunho")
    SENT = "sent", _("Enviado")
    NEGOTIATION = "negotiation", _("Em Negociação")
    ACCEPTED = "accepted", _("Aceito")
    REJECTED = "rejected", _("Recusado")
    CANCELLED = "cancelled", _("Cancelado")


class Quote(models.Model):
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="quotes",
        verbose_name=_("Conta"),
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="quotes",
        verbose_name=_("Cliente"),
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200, verbose_name=_("Título do Orçamento"))
    description = models.TextField(blank=True, verbose_name=_("Descrição"))

    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Valor da Hora")
    )
    work_hours = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Horas de Trabalho")
    )

    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Custo de Mão de Obra"),
    )
    expenses_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Custo de Despesas")
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Total")
    )

    notes = models.TextField(blank=True, verbose_name=_("Observações"))

    status = models.CharField(
        max_length=20,
        choices=QuoteStatus.choices,
        default=QuoteStatus.DRAFT,
        verbose_name=_("Status"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quotes"
        verbose_name = _("Orçamento")
        verbose_name_plural = _("Orçamentos")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def calculate(self):
        if not self.pk:
            return Decimal("0")
        self.labor_cost = self.hourly_rate * self.work_hours
        self.expenses_cost = sum(e.total for e in self.expenses.all())
        self.total = self.labor_cost + self.expenses_cost
        return self.total

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None

        if not is_new:
            old_quote = Quote.objects.get(pk=self.pk)
            old_status = old_quote.status

        if self.pk:
            self.calculate()

        super().save(*args, **kwargs)

        if (
            not is_new
            and old_status != QuoteStatus.SENT
            and self.status == QuoteStatus.SENT
        ):
            if self.client and self.client.email:
                from base.core.emails import send_quote_email

                send_quote_email(self, self.client.email)


class QuoteExpense(models.Model):
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name=_("Orçamento"),
    )
    description = models.CharField(max_length=200, verbose_name=_("Descrição"))
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=1, verbose_name=_("Quantidade")
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Preço Unitário")
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Total")
    )

    class Meta:
        db_table = "quote_expenses"
        verbose_name = _("Despesa do Orçamento")
        verbose_name_plural = _("Despesas do Orçamento")

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.quote.expenses_cost = sum(e.total for e in self.quote.expenses.all())
        self.quote.save()
