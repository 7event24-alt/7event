from rest_framework import serializers
from .models import Expense, ExpenseCategory


class ExpenseSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.get_full_name", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "performed_by",
            "performed_by_name",
            "job",
            "job_title",
            "category",
            "value",
            "date",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["performed_by"] = self.context["request"].user
        return super().create(validated_data)