from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import SupportMessage


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "subject",
        "is_read",
        "created_at",
        "responded_at",
        "action_buttons",
    ]
    list_filter = ["is_read", "subject", "created_at"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Informações do Remetente", {"fields": ("name", "email", "phone", "user")}),
        ("Mensagem", {"fields": ("subject", "message")}),
        ("Status", {"fields": ("is_read",)}),
        ("Resposta", {"fields": ("response", "responded_at", "responded_by")}),
        ("Sistema", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def action_buttons(self, obj):
        if obj.responded_at:
            return format_html(
                '<span class="text-green-600"><i class="fas fa-check"></i> Respondido</span>'
            )
        return format_html(
            '<a href="{}" class="button" style="background:#10b981;color:white;padding:6px 12px;border-radius:4px;text-decoration:none;font-size:12px;">'
            '<i class="fas fa-reply"></i> Responder</a>',
            reverse(f"admin:support_supportmessage_change", args=[obj.pk]),
        )

    action_buttons.short_description = "Ação"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save_and_continue"] = False
        extra_context["show_save"] = True
        extra_context["show_save_and_add_another"] = False
        extra_context["show_delete_link"] = True
        return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if obj.response and not obj.responded_at:
            obj.responded_at = timezone.now()
            obj.responded_by = request.user
            from base.core.emails import send_support_reply

            send_support_reply(obj)
        super().save_model(request, obj, form, change)
