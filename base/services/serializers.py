from rest_framework import serializers
from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    estimated_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "estimated_duration_hours",
            "hourly_rate",
            "typical_expenses",
            "estimated_total",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["account"] = self.context["request"].user.account
        return super().create(validated_data)
