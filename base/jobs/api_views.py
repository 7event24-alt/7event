from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Job
from .serializers import JobSerializer


class JobPermissions(permissions.BasePermission):
    message = "Você não tem permissão para acessar este trabalho."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.account:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return obj.account == request.user.account


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [JobPermissions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "payment_status", "event_type", "is_multi_day"]
    search_fields = ["title", "client__name", "location"]
    ordering_fields = ["start_date", "created_at", "cache"]
    ordering = ["-start_date"]

    def get_queryset(self):
        if not self.request.user.account:
            return Job.objects.none()
        return Job.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(account=self.request.user.account, user=self.request.user)
