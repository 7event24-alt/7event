from django.contrib import admin
from .models import Quote, QuoteExpense


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["title", "client", "total", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "client__name"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("client", "title", "description")}),
        ("Valores", {"fields": ("hourly_rate", "work_hours", "labor_cost", "expenses_cost", "total")}),
        ("Observações", {"fields": ("notes",)}),
        ("Status", {"fields": ("status", "is_active")}),
    )
    readonly_fields = ["labor_cost", "expenses_cost", "total"]


@admin.register(QuoteExpense)
class QuoteExpenseAdmin(admin.ModelAdmin):
    list_display = ["quote", "description", "quantity", "unit_price", "total"]
    search_fields = ["description", "quote__title"]