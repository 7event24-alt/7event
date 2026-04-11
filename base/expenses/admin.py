from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["job", "account", "category", "value", "date", "created_at"]
    list_filter = ["category", "date", "account"]
    search_fields = ["description", "job__title"]
    ordering = ["-date"]
    date_hierarchy = "date"
