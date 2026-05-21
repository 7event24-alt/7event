from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    User,
    Plan,
    Subscription,
    Feature,
    PlanType,
    BillingPeriod,
    SubscriptionStatus,
    PrivacyTerm,
    PersonalTaskReminderDispatch,
    SystemReminderDispatch,
)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "type",
        "price_monthly",
        "price_quarterly",
        "price_semester",
        "max_users",
        "can_associate_professionals",
        "is_active",
    ]
    list_filter = ["type", "is_active", "can_associate_professionals"]
    filter_horizontal = ["features"]
    fieldsets = (
        (None, {"fields": ("type", "name", "description", "short_description")}),
        (
            "Limites",
            {
                "fields": (
                    "max_users",
                    "max_clients",
                    "max_jobs",
                    "max_quotes",
                    "max_expenses",
                    "max_agenda_events",
                    "max_personal_tasks",
                    "max_personal_agenda_events",
                    "can_associate_professionals",
                    "job_creation_limit",
                )
            },
        ),
        ("Preços", {"fields": ("price_monthly", "price_quarterly", "price_semester")}),
        ("Pagamento", {"fields": ("payment_link", "is_visible", "highlight")}),
        ("Funcionalidades", {"fields": ("features", "is_active")}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "status", "billing_period", "price", "end_date"]
    list_filter = ["status", "billing_period"]
    fieldsets = (
        (None, {"fields": ("user", "plan")}),
        (
            "Cobrança",
            {
                "fields": (
                    "status",
                    "billing_period",
                    "price",
                    "start_date",
                    "end_date",
                    "next_billing_date",
                )
            },
        ),
        ("Pagamento", {"fields": ("payment_status", "last_payment_date")}),
    )


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "is_premium"]
    search_fields = ["name", "key"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "plan",
        "role",
        "is_active",
        "is_blocked",
        "actions_column",
    ]
    list_filter = [
        "is_active",
        "is_blocked",
        "role",
        "plan",
    ]
    search_fields = ["username", "email", "first_name", "last_name", "cnpj"]
    ordering = ["-created_at"]
    readonly_fields = ("created_at", "updated_at", "last_login")

    @admin.display(description="Ações")
    def actions_column(self, obj):
        if not obj.is_active:
            url = reverse("accounts:admin_resend_activation", args=[obj.pk])
            return format_html(
                '<a href="{}" class="button" title="Enviar email de ativação" style="color: #2563eb;">'
                '<i class="fas fa-envelope"></i> Enviar</a>',
                url,
            )
        return "-"

    def has_add_permission(self, request):
        return True

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Pessoal", {"fields": ("first_name", "last_name", "email", "phone", "photo")}),
        ("Empresa", {"fields": ("legal_name", "cnpj", "address", "company_logo")}),
        ("Plano", {"fields": ("plan",)}),
        ("Cargo", {"fields": ("role",)}),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                    "is_blocked",
                    "blocked_reason",
                    "blocked_at",
                    "notes",
                )
            },
        ),
    )

    add_fieldsets = (
        (None, {"fields": ("username", "password1", "password2")}),
        ("Pessoal", {"fields": ("first_name", "last_name", "email")}),
    )


@admin.register(PrivacyTerm)
class PrivacyTermAdmin(admin.ModelAdmin):
    list_display = ["version", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["version", "content"]
    fieldsets = (
        (None, {"fields": ("version", "is_active")}),
        ("Conteúdo", {"fields": ("content",)}),
    )
    readonly_fields = ["created_at"]


@admin.register(PersonalTaskReminderDispatch)
class PersonalTaskReminderDispatchAdmin(admin.ModelAdmin):
    list_display = ["task", "reminder_type", "sent_at"]
    list_filter = ["reminder_type", "sent_at"]
    search_fields = ["task__title", "task__user__email", "task__user__username"]
    readonly_fields = ["task", "reminder_type", "sent_at"]


@admin.register(SystemReminderDispatch)
class SystemReminderDispatchAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "entity_id", "reminder_type", "slot_date", "slot_label", "sent_at"]
    list_filter = ["entity_type", "reminder_type", "slot_label", "slot_date"]
    search_fields = ["entity_type", "entity_id", "reminder_type"]
    readonly_fields = ["entity_type", "entity_id", "reminder_type", "slot_date", "slot_label", "sent_at"]
