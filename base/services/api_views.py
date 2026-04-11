from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Service
from .serializers import ServiceSerializer


class ServicePermissions(permissions.BasePermission):
    message = "Você não tem permissão para acessar este serviço."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.account:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return obj.account == request.user.account


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [ServicePermissions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]
    lookup_field = "pk"

    def get_queryset(self):
        if not self.request.user.account:
            return Service.objects.none()
        return Service.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(account=self.request.user.account)
