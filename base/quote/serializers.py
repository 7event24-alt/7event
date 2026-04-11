from rest_framework import serializers
from .models import Quote, QuoteService, QuoteExpense


class QuoteServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = QuoteService
        fields = ["id", "service", "service_name", "quantity", "custom_price", "total"]
        read_only_fields = ["id"]


class QuoteExpenseSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = QuoteExpense
        fields = ["id", "description", "quantity", "unit_price", "total"]
        read_only_fields = ["id"]


class QuoteSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    services = QuoteServiceSerializer(many=True, read_only=True)
    expenses = QuoteExpenseSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id",
            "client",
            "client_name",
            "title",
            "description",
            "hourly_rate",
            "work_hours",
            "labor_cost",
            "expenses_cost",
            "total",
            "status",
            "status_display",
            "notes",
            "created_at",
            "updated_at",
            "services",
            "expenses",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class QuoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = [
            "client",
            "title",
            "description",
            "hourly_rate",
            "work_hours",
            "status",
            "notes",
        ]
