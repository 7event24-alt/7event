from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "hourly_rate",
        "estimated_duration_hours",
        "typical_expenses",
        "estimated_total",
        "is_active",
    ]
    list_filter = ["is_active", "account"]
    search_fields = ["name", "description"]

    fieldsets = (
        (None, {"fields": ("account", "name", "description")}),
        (
            "Estimativas",
            {"fields": ("estimated_duration_hours", "hourly_rate", "typical_expenses")},
        ),
        ("Status", {"fields": ("is_active",)}),
    )

    readonly_fields = ["estimated_total"]

    def estimated_total(self, obj):
        return f"R$ {obj.estimated_total:f}"

    estimated_total.short_description = "Total Estimado"
