from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class EventType(models.TextChoices):
    CORPORATIVO = "corporativo", _("Corporativo")
    FEIRAS_EXPOSICOES = "feiras_exposicoes", _("Feiras e Exposições")
    SHOWS_FESTIVAIS = "shows_festivais", _("Shows e Festivais")
    TEATRO = "teatro", _("Teatro")
    GRAVACAO_DVD = "gravacao_dvd", _("Gravação de DVD")
    PODCASTS = "podcasts", _("Podcasts")
    PRODUCAO_CONTEUDO = "producao_conteudo", _("Produção de Conteúdo")
    EVENTOS = "eventos", _("Eventos")
    EVENTOS_SOCIAIS = "eventos_sociais", _("Eventos Sociais")
    INTERNET = "internet", _("Internet")
    LIVES = "lives", _("Lives / Transmissões ao Vivo")
    COLETIVAS_IMPRENSA = "coletivas_imprensa", _("Coletivas de Imprensa")
    PROGRAMAS_TV = "programas_tv", _("Programas de Televisão / Reality")
    DOCUMENTARIOS = "documentarios", _("Documentários")
    CAMPANHA_PUBLICITARIA = "campanha_publicitaria", _("Campanha Publicitária")


class JobStatus(models.TextChoices):
    PENDING = "pending", _("Pendente")
    CONFIRMED = "confirmed", _("Confirmado")
    COMPLETED = "completed", _("Concluído")
    CANCELLED = "cancelled", _("Cancelado")


class PaymentType(models.TextChoices):
    ADVANCE = "advance", _("Pagamento Antecipado")
    FULL = "full", _("Pagamento Total")
    PARTIAL = "partial", _("Pagamento Parcial")


class PaymentStatusJob(models.TextChoices):
    PENDING = "pending", _("Pendente")
    PARTIAL = "partial", _("Parcial")
    PAID = "paid", _("Pago")


class Job(models.Model):
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="jobs",
        verbose_name=_("Conta"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="jobs_created",
        verbose_name=_("Criado por"),
        null=True,
        blank=True,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="jobs",
        verbose_name=_("Cliente"),
    )

    title = models.CharField(max_length=200, verbose_name=_("Título"))
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        default=EventType.CORPORATIVO,
        verbose_name=_("Tipo de Serviço"),
    )

    start_date = models.DateField(
        null=True, blank=True, verbose_name=_("Data do Evento")
    )
    end_date = models.DateField(null=True, blank=True, verbose_name=_("Data Final"))
    start_time = models.TimeField(null=True, blank=True, verbose_name=_("Hora Inicial"))
    end_time = models.TimeField(null=True, blank=True, verbose_name=_("Hora Final"))

    location = models.CharField(max_length=300, blank=True, verbose_name=_("Local"))
    description = models.TextField(blank=True, verbose_name=_("Descrição"))

    cache = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Cachê")
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.FULL,
        verbose_name=_("Tipo de Pagamento"),
    )
    payment_date = models.DateField(
        null=True, blank=True, verbose_name=_("Data de Pagamento")
    )
    payment_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Valor Total"),
    )
    payment_partial_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Valor Parcial"),
    )
    payment_partial_date = models.DateField(
        null=True, blank=True, verbose_name=_("Data Pagamento Parcial")
    )
    payment_remaining_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Valor Restante"),
    )
    payment_remaining_date = models.DateField(
        null=True, blank=True, verbose_name=_("Data Pagamento Restante")
    )

    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
        verbose_name=_("Status do Evento"),
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatusJob.choices,
        default=PaymentStatusJob.PENDING,
        verbose_name=_("Status de Pagamento"),
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_jobs",
        verbose_name="Aprovado por",
    )
    approved_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Data da Aprovação"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobs"
        verbose_name = _("Trabalho")
        verbose_name_plural = _("Trabalhos")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.title} - {self.client.name}"

    @property
    def total_expenses(self):
        return sum(expense.value for expense in self.expenses.all())

    @property
    def net_profit(self):
        return (self.cache or 0) - self.total_expenses

    @property
    def is_single_day(self):
        return not self.end_date or self.end_date == self.start_date

    @property
    def duration_days(self):
        if self.end_date and self.end_date != self.start_date:
            return (self.end_date - self.start_date).days + 1
        return 1

    @property
    def is_past_event(self):
        from django.utils import timezone

        return self.start_date < timezone.now().date()

    def calculate_payment_values(self):
        """Calcula automaticamente os valores de pagamento baseados no cache e tipo de pagamento"""
        if not self.cache:
            return

        # O payment_total SEMPRE deve ser igual ao cache
        self.payment_total = self.cache

        if self.payment_type == PaymentType.FULL:
            # Pagamento total - não precisa de valores parciais/restantes
            self.payment_partial_value = None
            self.payment_partial_date = None
            self.payment_remaining_value = None
            self.payment_remaining_date = None

        elif self.payment_type == PaymentType.PARTIAL:
            # Pagamento parcial - o restante é calculado automaticamente
            if self.payment_partial_value:
                self.payment_remaining_value = self.cache - self.payment_partial_value
            else:
                self.payment_remaining_value = self.cache

        elif self.payment_type == PaymentType.ADVANCE:
            # Pagamento antecipado - o restante é calculado automaticamente
            if self.payment_partial_value:
                self.payment_remaining_value = self.cache - self.payment_partial_value
            else:
                self.payment_remaining_value = self.cache

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()

        if (
            self.payment_type == PaymentType.PARTIAL
            and self.payment_partial_value
            and self.cache
        ):
            if self.payment_partial_value > self.cache:
                raise ValidationError(
                    {
                        "payment_partial_value": "Valor parcial não pode ser maior que o cachê."
                    }
                )

    def save(self, *args, **kwargs):
        # Calcular valores de pagamento automaticamente antes de salvar
        self.calculate_payment_values()
        super().save(*args, **kwargs)
