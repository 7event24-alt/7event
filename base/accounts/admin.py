from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Account,
    Plan,
    Subscription,
    Feature,
    AccountType,
    PlanType,
    BillingPeriod,
    SubscriptionStatus,
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "account_type",
        "plan",
        "is_active",
        "is_blocked",
        "user_count",
    ]
    list_filter = ["account_type", "is_active", "is_blocked"]
    search_fields = ["name", "slug", "cnpj"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (None, {"fields": ("account_type", "name", "slug")}),
        ("Documentos", {"fields": ("cnpj", "phone", "email")}),
        ("Endereço", {"fields": ("address", "logo")}),
        ("Plano", {"fields": ("plan",)}),
        ("Status", {"fields": ("is_active", "is_blocked", "blocked_reason")}),
    )

    readonly_fields = ["user_count"]

    def user_count(self, obj):
        return obj.user_count

    user_count.short_description = "Usuários"


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "type",
        "price_monthly",
        "price_quarterly",
        "price_semester",
        "max_users",
        "is_active",
    ]
    list_filter = ["type", "is_active"]
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
                    "max_expenses",
                    "max_agenda_events",
                )
            },
        ),
        ("Preços", {"fields": ("price_monthly", "price_quarterly", "price_semester")}),
        ("Pagamento", {"fields": ("payment_link", "is_visible", "highlight")}),
        ("Funcionalidades", {"fields": ("features", "is_active")}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["account", "plan", "status", "billing_period", "price", "end_date"]
    list_filter = ["status", "billing_period"]
    fieldsets = (
        (None, {"fields": ("account", "plan")}),
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
        "account",
        "plan",
        "role",
        "is_account_admin",
        "is_active",
        "is_blocked",
    ]
    list_filter = [
        "is_active",
        "is_blocked",
        "is_account_admin",
        "account",
        "role",
        "plan",
    ]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-created_at"]
    readonly_fields = ("created_at", "updated_at", "last_login")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Pessoal", {"fields": ("first_name", "last_name", "email", "phone", "photo")}),
        ("Conta", {"fields": ("account", "role", "is_account_admin", "plan")}),
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
        ("Conta", {"fields": ("account", "role", "is_account_admin")}),
    )
