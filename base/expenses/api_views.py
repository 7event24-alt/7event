from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Expense
from .serializers import ExpenseSerializer


class ExpensePermissions(permissions.BasePermission):
    message = "Você não tem permissão para acessar esta despesa."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.account:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return obj.account == request.user.account


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [ExpensePermissions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "job", "date"]
    search_fields = ["description", "job__title"]
    ordering_fields = ["date", "value", "created_at"]
    ordering = ["-date"]

    def get_queryset(self):
        if not self.request.user.account:
            return Expense.objects.none()
        return Expense.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(account=self.request.user.account, user=self.request.user)
