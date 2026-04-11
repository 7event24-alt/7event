from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client
from .serializers import ClientSerializer


class ClientPermissions(permissions.BasePermission):
    message = "Você não tem permissão para acessar este cliente."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.account:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return obj.account == request.user.account


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [ClientPermissions]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name", "email", "phone", "document"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        if not self.request.user.account:
            return Client.objects.none()
        return Client.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(account=self.request.user.account)
