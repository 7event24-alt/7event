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
    ASSISTENTE_CAMERA = "assistente_camera", _("Assistente de Câmera")
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


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        return super().create_superuser(username, email, password, **extra_fields)


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

    can_associate_professionals = models.BooleanField(
        default=False, verbose_name=_("Pode Associar Profissionais")
    )
    job_creation_limit = models.IntegerField(
        default=-1, verbose_name=_("Limite de Criação de Jobs (-1 = ilimitado)")
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
        # Tenta primeiro pelo tipo BASIC
        plan = cls.objects.filter(type=PlanType.BASIC, is_active=True).first()
        if plan:
            return plan
        # Tenta encontrar plano com nome contendo 'Free' ou 'Grátis'
        plan = cls.objects.filter(name__icontains='Free', is_active=True).first()
        if plan:
            return plan
        plan = cls.objects.filter(name__icontains='Grátis', is_active=True).first()
        if plan:
            return plan
        # Fallback: qualquer plano ativo
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def get_tester(cls):
        return cls.objects.filter(type=PlanType.TESTER, is_active=True).first()

    @property
    def is_agency_plan(self):
        return self.can_associate_professionals


class Subscription(models.Model):
    user = models.OneToOneField(
        "User",
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name=_("Usuário"),
        null=True,
        blank=True,
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
    start_date = models.DateField(null=True, blank=True, verbose_name=_("Início"))
    end_date = models.DateField(null=True, blank=True, verbose_name=_("Fim"))
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
        return f"{self.user.username} - {self.plan.name if self.plan else 'Sem plano'}"

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

    email = models.EmailField(blank=True, unique=True, verbose_name=_("Email"))

    # Dados sensíveis (LGPD)
    full_name = models.CharField(max_length=200, blank=True, verbose_name=_("Nome Completo"))
    cpf = models.CharField(max_length=14, blank=True, verbose_name=_("CPF"))
    rg = models.CharField(max_length=20, blank=True, verbose_name=_("RG"))

    legal_name = models.CharField(
        max_length=200, blank=True, verbose_name=_("Nome Fantasia / Razão Social")
    )
    cnpj = models.CharField(max_length=18, blank=True, verbose_name=_("CNPJ"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Telefone"))
    address = models.TextField(blank=True, verbose_name=_("Endereço"))
    company_logo = models.ImageField(
        upload_to="users/logos/", blank=True, null=True, verbose_name=_("Logo da Empresa")
    )

    photo = models.ImageField(
        upload_to="users/%Y/%m/", blank=True, null=True, verbose_name=_("Foto")
    )
    role = models.CharField(
        max_length=50,
        choices=ProfessionalRole.choices,
        blank=True,
        verbose_name=_("Função/Cargo"),
    )

    # Campos Profissionais
    bio = models.TextField(blank=True, verbose_name=_("Biografia"))
    skills = models.CharField(max_length=500, blank=True, verbose_name=_("Habilidades"))
    portfolio_url = models.URLField(blank=True, verbose_name=_("URL do Portfólio"))

    # Controle de Privacidade
    show_sensitive_data = models.BooleanField(
        default=False, verbose_name=_("Permitir visualização de dados sensíveis")
    )
    accepted_term = models.ForeignKey(
        "PrivacyTerm",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users_accepted",
        verbose_name=_("Termo aceito"),
    )

    plan = models.ForeignKey(
        "Plan",
        on_delete=models.SET_NULL,
        related_name="users_with_plan",
        verbose_name=_("Plano"),
        null=True,
        blank=True,
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

    def get_plan(self):
        if self.plan:
            return self.plan
        default_plan = Plan.get_default()
        if default_plan:
            return default_plan
        # Fallback: cria um plano BASIC padrão se não existir nenhum
        default_plan, created = Plan.objects.get_or_create(
            type=PlanType.BASIC,
            defaults={
                'name': 'Básico',
                'is_active': True,
                'max_users': 1,
                'max_clients': 10,
                'max_jobs': 10,
                'max_expenses': 10,
                'max_agenda_events': 10,
                'can_associate_professionals': False,
                'job_creation_limit': -1,
            }
        )
        return default_plan

    def get_max_users(self):
        return self.get_plan().max_users

    def get_max_clients(self):
        return self.get_plan().max_clients

    def get_max_jobs(self):
        return self.get_plan().max_jobs

    def get_max_expenses(self):
        return self.get_plan().max_expenses

    def get_max_agenda_events(self):
        return self.get_plan().max_agenda_events

    def can_associate_professionals(self):
        return self.get_plan().can_associate_professionals

    def has_limit(self, model_class, current_count):
        plan = self.get_plan()
        if model_class.__name__ == "Client":
            max_count = plan.max_clients if plan.max_clients > 0 else float("inf")
        elif model_class.__name__ == "Job":
            max_count = plan.max_jobs if plan.max_jobs > 0 else float("inf")
        elif model_class.__name__ == "Expense":
            max_count = plan.max_expenses if plan.max_expenses > 0 else float("inf")
        else:
            return False
        return current_count >= max_count

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

        cutoff = timezone.now() - timedelta(minutes=30)
        Notification.objects.filter(user=self.user, created_at__lt=cutoff).delete()


class PrivacyTerm(models.Model):
    version = models.CharField(max_length=20, unique=True, verbose_name=_("Versão"))
    content = models.TextField(verbose_name=_("Conteúdo"))
    is_active = models.BooleanField(default=False, verbose_name=_("Ativo"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))

    class Meta:
        db_table = "privacy_terms"
        verbose_name = _("Termo de Privacidade")
        verbose_name_plural = _("Termos de Privacidade")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Termo v{self.version}"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Desativa outros termos ativos
            PrivacyTerm.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class FCMToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="fcm_tokens",
        verbose_name=_("Usuário"),
    )
    token = models.CharField(max_length=500, verbose_name=_("Token P256DH"), blank=True)
    auth = models.CharField(max_length=100, verbose_name=_("Token Auth"), blank=True)
    subscription = models.TextField(verbose_name=_("Subscription JSON"), blank=True)
    device_type = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Tipo do Dispositivo"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Ativo"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Atualizado em"))

    class Meta:
        db_table = "fcm_tokens"
        verbose_name = _("Token FCM")
        verbose_name_plural = _("Tokens FCM")
        unique_together = [["user", "device_type"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"FCM Token - {self.user.username} ({self.device_type})"


class PersonalTask(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="personal_tasks",
        verbose_name=_("Usuário")
    )
    title = models.CharField(max_length=200, verbose_name=_("Título da Tarefa"))
    date = models.DateField(verbose_name=_("Data"))
    time = models.TimeField(null=True, blank=True, verbose_name=_("Horário"))
    is_completed = models.BooleanField(default=False, verbose_name=_("Concluída"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criada em"))

    class Meta:
        db_table = "personal_tasks"
        verbose_name = _("Tarefa Pessoal")
        verbose_name_plural = _("Tarefas Pessoais")
        ordering = ["date", "time"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "is_completed"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"