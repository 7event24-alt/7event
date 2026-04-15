from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.utils.translation import gettext_lazy as _


class ProfessionalRole(models.TextChoices):
    DIRETOR_EVENTO = "diretor_evento", _("Diretor de Evento / Event Manager")
    PRODUTOR_EXECUTIVO = "produtor_executivo", _("Produtor Executivo")
    COORDENADOR_GERAL = "coordenador_geral", _("Coordenador Geral")
    GERENTE_PROJETO = "gerente_projeto", _("Gerente de Projeto")
    ASSISTENTE_PRODUCAO = "assistente_producao", _("Assistente de Produção")
    DIRETOR_TECNICO = "diretor_tecnico", _("Diretor Técnico")
    COORDENADOR_TECNICO = "coordenador_tecnico", _("Coordenador Técnico")
    STAGE_MANAGER = "stage_manager", _("Stage Manager (gerente de palco)")
    ROADIE = "roadie", _("Roadie / Assistente de palco")
    RIGGER = "rigger", _("Rigger (montagem aérea)")
    TECNICO_MONTAGEM = "tecnico_montagem", _("Técnico de montagem")
    DIRETOR_FOTOGRAFIA = "diretor_fotografia", _("Diretor de Fotografia")
    OPERADOR_CAMERA = "operador_camera", _("Operador de Câmera")
    TECNICO_VIDEO = "tecnico_video", _("Técnico de Vídeo")
    OPERADOR_SWITCHER = "operador_switcher", _("Operador de Switcher")
    TECNICO_STREAMING = "tecnico_streaming", _("Técnico de Streaming / Live")
    TECNICO_LED = "tecnico_led", _("Técnico de LED / Painel de LED")
    EDITOR_VIDEO = "editor_video", _("Editor de Vídeo")
    TECNICO_PROJECAO = "tecnico_projecao", _("Técnico de Projeção")
    TECNICO_SOM = "tecnico_som", _("Técnico de Som (PA)")
    OPERADOR_MESA_AUDIO = "operador_mesa_audio", _("Operador de Mesa de Áudio")
    TECNICO_MONITOR = "tecnico_monitor", _("Técnico de Monitor")
    MICROFONISTA = "microfonista", _("Microfonista")
    ENGENHEIRO_AUDIO = "engenheiro_audio", _("Engenheiro de Áudio")
    LIGHTING_DESIGNER = "lighting_designer", _("Lighting Designer")
    TECNICO_ILUMINACAO = "tecnico_iluminacao", _("Técnico de Iluminação")
    OPERADOR_MESA_LUZ = "operador_mesa_luz", _("Operador de Mesa de Luz")
    PROGRAMADOR_LUZ = "programador_luz", _("Programador de luz")
    CENOGRAFO = "cenografo", _("Cenógrafo")
    MONTADOR_ESTRUTURA = "montador_estrutura", _("Montadores de estrutura")
    CARPINTEIRO = "carpinteiro", _("Carpinteiros / Serralheiros")
    TECNICO_STANDS = "tecnico_stands", _("Técnico de Stands (feiras)")
    RECEPCIONISTA = "recepcionista", _("Recepcionistas")
    CREDENCIAMENTO = "credenciamento", _("Credenciamento")
    HOSTESS = "hostess", _("Hostess / Promotores")
    STAFF_APOIO = "staff_apoio", _("Staff de apoio")
    BRIGADISTA = "brigadista", _("Brigadistas")
    SEGURANCA = "seguranca", _("Segurança")
    COORDENADOR_MARKETING = "coordenador_marketing", _("Coordenador de Marketing")
    SOCIAL_MEDIA = "social_media", _("Social Media")
    FOTOGRAFO = "fotografo", _("Fotógrafo")
    ASSESSORIA_IMPRENSA = "assessoria_imprensa", _("Assessoria de Imprensa")
    DESIGNER = "designer", _("Designer")
    CATERING = "catering", _("Catering / Buffet")
    GARCOM_BARTENDER = "garcom_bartender", _("Garçons / Bartenders")
    LIMPEZA = "limpeza", _("Limpeza")
    TRANSPORTE = "transporte", _("Transporte")
    MOTORISTA = "motorista", _("Motoristas")
    EXECUTIVO_COMERCIAL = "executivo_comercial", _("Executivo Comercial")
    ATENDIMENTO_CLIENTE = "atendimento_cliente", _("Atendimento ao Cliente")
    CAPTACAO_PATROCINIO = "captacao_patrocinio", _("Captação de Patrocínio")
    RELACIONAMENTO_EXPOSITORES = (
        "relacionamento_expositores",
        _("Relacionamento com Expositores"),
    )
    TECNICO_SEGURANCA_TRABALHO = (
        "tecnico_seguranca_trabalho",
        _("Técnico de Segurança do Trabalho"),
    )
    BOMBEIRO_CIVIL = "bombeiro_civil", _("Bombeiro Civil")
    RESPONSAVEL_TECNICO = "responsavel_tecnico", _("Responsável Técnico")
    EQUIPE_MEDICA = "equipe_medica", _("Equipe médica / ambulância")
    CONVIDADO = "convidado", _("Convidado")


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        return super().create_superuser(username, email, password, **extra_fields)


class AccountType(models.TextChoices):
    AUTONOMOUS = "autonomous", _("Autônomo")
    COMPANY = "company", _("Empresa")


class PlanType(models.TextChoices):
    TESTER = "tester", _("Teste")
    BASIC = "basic", _("Básico")
    BUSINESS = "business", _("Business")


class BillingPeriod(models.TextChoices):
    MONTHLY = "monthly", _("Mensal")
    QUARTERLY = "quarterly", _("Trimestral")
    SEMESTER = "semester", _("Semestral")


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", _("Ativo")
    TRIAL = "trial", _("Trial")
    EXPIRED = "expired", _("Expirado")
    OVERDUE = "overdue", _("Atrasado")
    CANCELLED = "cancelled", _("Cancelado")


class Feature(models.Model):
    key = models.CharField(max_length=50, unique=True, verbose_name=_("Chave"))
    name = models.CharField(max_length=100, verbose_name=_("Nome"))
    description = models.TextField(blank=True, verbose_name=_("Descrição"))
    is_premium = models.BooleanField(default=False, verbose_name=_("Premium"))

    class Meta:
        verbose_name = _("Funcionalidade")
        verbose_name_plural = _("Funcionalidades")

    def __str__(self):
        return self.name


class Plan(models.Model):
    type = models.CharField(
        max_length=20, choices=PlanType.choices, unique=True, verbose_name=_("Tipo")
    )
    name = models.CharField(max_length=100, verbose_name=_("Nome"))
    description = models.TextField(blank=True, verbose_name=_("Descrição"))
    short_description = models.CharField(
        max_length=200, blank=True, verbose_name=_("Descrição Curta")
    )

    max_users = models.PositiveIntegerField(
        default=1, verbose_name=_("Máximo de Usuários")
    )
    max_clients = models.PositiveIntegerField(
        default=10, verbose_name=_("Máximo de Clientes")
    )
    max_jobs = models.PositiveIntegerField(
        default=10, verbose_name=_("Máximo de Trabalhos")
    )
    max_expenses = models.PositiveIntegerField(
        default=10, verbose_name=_("Máximo de Despesas")
    )
    max_agenda_events = models.PositiveIntegerField(
        default=10, verbose_name=_("Máximo de Eventos")
    )

    price_monthly = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Preço Mensal")
    )
    price_quarterly = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Preço Trimestral")
    )
    price_semester = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Preço Semestral")
    )

    payment_link = models.URLField(blank=True, verbose_name=_("Link de Pagamento"))
    is_visible = models.BooleanField(default=True, verbose_name=_("Visível no Site"))
    highlight = models.BooleanField(
        default=False, verbose_name=_("Destaque (Recomendado)")
    )

    features = models.ManyToManyField(
        Feature, blank=True, verbose_name=_("Funcionalidades")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Ativo"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "plans"
        verbose_name = _("Plano")
        verbose_name_plural = _("Planos")
        ordering = ["price_monthly"]

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls):
        return cls.objects.filter(type=PlanType.BASIC, is_active=True).first()

    @classmethod
    def get_tester(cls):
        return cls.objects.filter(type=PlanType.TESTER, is_active=True).first()


class Account(models.Model):
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.AUTONOMOUS,
        verbose_name=_("Tipo de Conta"),
    )
    name = models.CharField(max_length=200, verbose_name=_("Nome"))
    slug = models.SlugField(max_length=50, unique=True, verbose_name=_("Slug"))
    cnpj = models.CharField(max_length=18, blank=True, verbose_name=_("CNPJ"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Telefone"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    address = models.TextField(blank=True, verbose_name=_("Endereço"))
    logo = models.ImageField(
        upload_to="accounts/logos/", blank=True, null=True, verbose_name=_("Logo")
    )

    notify_on_job_created = models.BooleanField(
        default=True, verbose_name=_("Notificar ao criar trabalho")
    )
    notify_on_job_confirmed = models.BooleanField(
        default=True, verbose_name=_("Notificar cliente ao confirmar trabalho")
    )
    notify_on_client_created = models.BooleanField(
        default=True, verbose_name=_("Notificar ao criar cliente")
    )
    notify_on_service_created = models.BooleanField(
        default=True, verbose_name=_("Notificar ao criar serviço")
    )
    notify_on_expense_created = models.BooleanField(
        default=True, verbose_name=_("Notificar ao criar despesa")
    )
    notify_on_quote_created = models.BooleanField(
        default=True, verbose_name=_("Notificar ao criar orçamento")
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts",
        verbose_name=_("Plano"),
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Ativa"))
    is_blocked = models.BooleanField(default=False, verbose_name=_("Bloqueada"))
    blocked_reason = models.TextField(blank=True, verbose_name=_("Motivo do Bloqueio"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts"
        verbose_name = _("Conta")
        verbose_name_plural = _("Contas")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def user_count(self):
        return self.users.count()

    @property
    def can_access(self):
        if self.is_blocked:
            return False
        if hasattr(self, "subscription"):
            if self.subscription.status in [
                SubscriptionStatus.OVERDUE,
                SubscriptionStatus.CANCELLED,
            ]:
                return False
        return True

    @property
    def is_at_user_limit(self):
        if not self.plan:
            return True
        return self.user_count >= self.plan.max_users

    def has_feature(self, feature_key):
        if not self.plan:
            return False
        if self.plan.type == PlanType.TESTER:
            return True
        return self.plan.features.filter(key=feature_key).exists()

    def can_add_user(self):
        if not self.plan:
            return False
        if self.is_at_user_limit:
            return False
        return self.can_access


class Subscription(models.Model):
    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name=_("Conta"),
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.SET_NULL, null=True, verbose_name=_("Plano")
    )

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
        verbose_name=_("Status"),
    )
    billing_period = models.CharField(
        max_length=20,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY,
        verbose_name=_("Período"),
    )

    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Valor")
    )
    start_date = models.DateField(verbose_name=_("Início"))
    end_date = models.DateField(verbose_name=_("Fim"))
    next_billing_date = models.DateField(
        null=True, blank=True, verbose_name=_("Próxima Cobrança")
    )

    payment_status = models.CharField(
        max_length=20, blank=True, verbose_name=_("Status do Pagamento")
    )
    last_payment_date = models.DateField(
        null=True, blank=True, verbose_name=_("Último Pagamento")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions"
        verbose_name = _("Assinatura")
        verbose_name_plural = _("Assinaturas")

    def __str__(self):
        return f"{self.account.name} - {self.plan.name if self.plan else 'Sem plano'}"

    def is_active(self):
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]

    def is_expired(self):
        from django.utils import timezone

        return self.end_date < timezone.now().date() if self.end_date else False

    def days_until_expiry(self):
        from django.utils import timezone

        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return delta.days
        return None


class User(AbstractUser):
    objects = UserManager()

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="users",
        verbose_name=_("Conta"),
        null=True,
        blank=True,
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Telefone"))
    photo = models.ImageField(
        upload_to="users/%Y/%m/", blank=True, null=True, verbose_name=_("Foto")
    )
    role = models.CharField(
        max_length=50,
        choices=ProfessionalRole.choices,
        blank=True,
        verbose_name=_("Função/Cargo"),
    )

    is_account_admin = models.BooleanField(
        default=False, verbose_name=_("É Admin da Conta")
    )
    is_verified = models.BooleanField(default=False, verbose_name=_("Email Verificado"))
    verification_token = models.CharField(
        max_length=64, blank=True, verbose_name=_("Token de Verificação")
    )
    invite_token = models.CharField(
        max_length=64, blank=True, verbose_name=_("Token de Convite")
    )
    invited_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_users",
        verbose_name=_("Convidado por"),
    )
    is_blocked = models.BooleanField(default=False, verbose_name=_("Bloqueado"))
    blocked_reason = models.TextField(blank=True, verbose_name=_("Motivo do Bloqueio"))
    blocked_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Bloqueado em")
    )

    notes = models.TextField(blank=True, verbose_name=_("Anotações"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        verbose_name = _("Usuário")
        verbose_name_plural = _("Usuários")
        ordering = ["-created_at"]


class NotificationType(models.TextChoices):
    JOB = "job", _("Trabalho")
    CLIENT = "client", _("Cliente")
    SERVICE = "service", _("Serviço")
    EXPENSE = "expense", _("Despesa")
    QUOTE = "quote", _("Orçamento")
    SYSTEM = "system", _("Sistema")


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Usuário"),
    )
    title = models.CharField(max_length=100, verbose_name=_("Título"))
    message = models.CharField(max_length=255, verbose_name=_("Mensagem"))
    action_url = models.CharField(
        max_length=255, blank=True, verbose_name=_("URL de Ação")
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    is_read = models.BooleanField(default=False, verbose_name=_("Lida"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criada em"))

    class Meta:
        db_table = "notifications"
        verbose_name = _("Notificação")
        verbose_name_plural = _("Notificações")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from datetime import timedelta
        from django.utils import timezone

        cutoff = timezone.now() - timedelta(days=1)
        Notification.objects.filter(user=self.user, created_at__lt=cutoff).delete()

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    @property
    def can_access(self):
        if self.is_blocked:
            return False
        if hasattr(self, "subscription"):
            if self.subscription.status in [
                SubscriptionStatus.OVERDUE,
                SubscriptionStatus.CANCELLED,
            ]:
                return False
        return True

    @property
    def company(self):
        return self

    @property
    def max_users(self):
        return self.plan.max_users if self.plan else 1

    @property
    def get_plan_display(self):
        return self.plan.name if self.plan else "Sem Plano"
        if not self.account:
            return False
        if self.is_blocked:
            return False
        if not self.account.can_access:
            return False
        return True

    @property
    def is_account_owner(self):
        return self.is_account_admin or self.is_superuser

    @property
    def company(self):
        return self.account


Company = Account


class CompanyManager(models.Manager):
    def get_queryset(self):
        return Account.objects.all()

    def all(self):
        return Account.objects.all()

    def filter(self, *args, **kwargs):
        return Account.objects.filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        return Account.objects.get(*args, **kwargs)
