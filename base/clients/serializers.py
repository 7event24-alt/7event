from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    jobs_count = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Client
        fields = [
            "id",
            "account",
            "name",
            "email",
            "phone",
            "document",
            "address",
            "notes",
            "jobs_count",
            "total_revenue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["account"] = self.context["request"].user.account
        return super().create(validated_data)
