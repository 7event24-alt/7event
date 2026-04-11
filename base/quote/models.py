from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


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
        services_total = sum(s.total for s in self.services.all())
        self.labor_cost = self.hourly_rate * self.work_hours
        self.expenses_cost = sum(e.total for e in self.expenses.all())
        self.total = services_total + self.labor_cost + self.expenses_cost
        return self.total

    def save(self, *args, **kwargs):
        if self.pk:
            self.calculate()
        super().save(*args, **kwargs)


class QuoteService(models.Model):
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("Orçamento"),
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        related_name="quote_services",
        verbose_name=_("Serviço"),
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantidade"))
    custom_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Preço Customizado"),
    )

    class Meta:
        db_table = "quote_services"
        verbose_name = _("Serviço do Orçamento")
        verbose_name_plural = _("Serviços do Orçamento")

    def __str__(self):
        return f"{self.service.name} x{self.quantity}"

    @property
    def unit_price(self):
        if self.custom_price:
            return self.custom_price
        return self.service.hourly_rate * self.service.estimated_duration_hours

    @property
    def total(self):
        return self.unit_price * self.quantity


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
