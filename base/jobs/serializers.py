from rest_framework import serializers
from .models import Job, EventType, JobStatus, PaymentStatusJob


class JobSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    total_expenses = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    net_profit = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    duration_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "created_by",
            "created_by_name",
            "client",
            "client_name",
            "title",
            "event_type",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "location",
            "description",
            "total_budget",
            "cache",
            "payment_date",
            "status",
            "payment_status",
            "total_expenses",
            "net_profit",
            "duration_days",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)