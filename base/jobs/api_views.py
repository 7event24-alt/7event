from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Job
from .serializers import JobSerializer


class JobPermissions(permissions.BasePermission):
    message = "Você não tem permissão para acessar este trabalho."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.created_by == request.user


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [JobPermissions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "payment_status", "event_type"]
    search_fields = ["title", "client__name", "location"]
    ordering_fields = ["start_date", "created_at", "cache"]
    ordering = ["-start_date"]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Job.objects.all()
        return Job.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)