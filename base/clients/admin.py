from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "created_by", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "email", "phone", "document"]
    ordering = ["name"]

    fieldsets = (
        (None, {"fields": ("created_by", "name", "email", "phone")}),
        ("Documento", {"fields": ("document",), "classes": ("collapse",)}),
        ("Endereço", {"fields": ("address",), "classes": ("collapse",)}),
        ("Observações", {"fields": ("notes",)}),
    )