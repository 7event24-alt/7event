from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class SupportSubject(models.TextChoices):
    LOGIN = "login", _("Problemas de Login")
    CADASTRO = "cadastro", _("Problemas de Cadastro")
    TRABALHOS = "trabalhos", _("Dúvidas sobre Trabalhos")
    ORCAMENTOS = "orcamentos", _("Dúvidas sobre Orçamentos")
    PLANOS = "planos", _("Dúvidas sobre Planos")
    FINANCEIRO = "financeiro", _("Problemas Financeiros")
    BUG = "bug", _("Reportar Bug")
    OUTRO = "outro", _("Outro")


class SupportMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nome"))
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Telefone"))

    subject = models.CharField(
        max_length=30,
        choices=SupportSubject.choices,
        default=SupportSubject.OUTRO,
        verbose_name=_("Assunto"),
    )
    message = models.TextField(verbose_name=_("Mensagem"))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_messages",
        verbose_name=_("Usuário (se logado)"),
    )

    is_read = models.BooleanField(default=False, verbose_name=_("Lida"))

    response = models.TextField(blank=True, verbose_name=_("Resposta"))
    responded_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Respondido em")
    )
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_responses",
        verbose_name=_("Respondido por"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))

    class Meta:
        db_table = "support_messages"
        verbose_name = _("Mensagem de Suporte")
        verbose_name_plural = _("Mensagens de Suporte")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} - {self.created_at.strftime('%d/%m/%Y')}"
