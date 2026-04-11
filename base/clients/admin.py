from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "account", "created_at"]
    list_filter = ["account", "created_at"]
    search_fields = ["name", "email", "phone", "document"]
    ordering = ["name"]

    fieldsets = (
        (None, {"fields": ("account", "name", "email", "phone")}),
        ("Documento", {"fields": ("document",), "classes": ("collapse",)}),
        ("Endereço", {"fields": ("address",), "classes": ("collapse",)}),
        ("Observações", {"fields": ("notes",)}),
    )
