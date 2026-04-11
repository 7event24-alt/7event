from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Quote, QuoteService, QuoteExpense
from .serializers import QuoteSerializer, QuoteCreateSerializer


class QuotePermissions(permissions.BasePermission):
    message = "Você não tem permissão para acessar este orçamento."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not request.user.account:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return obj.account == request.user.account


class QuoteViewSet(viewsets.ModelViewSet):
    queryset = Quote.objects.all()
    permission_classes = [QuotePermissions]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "client"]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.action == "create":
            return QuoteCreateSerializer
        return QuoteSerializer

    def get_queryset(self):
        if not self.request.user.account:
            return Quote.objects.none()
        return Quote.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        serializer.save(account=self.request.user.account, user=self.request.user)

    @action(detail=True, methods=["post"])
    def add_service(self, request, pk=None):
        quote = self.get_object()
        service_id = request.data.get("service")
        quantity = request.data.get("quantity", 1)
        custom_price = request.data.get("custom_price")

        from base.services.models import Service

        try:
            service = Service.objects.get(id=service_id, account=request.user.account)
        except Service.DoesNotExist:
            return Response(
                {"error": "Serviço não encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        quote_service = QuoteService.objects.create(
            quote=quote,
            service=service,
            quantity=quantity,
            custom_price=custom_price,
        )
        quote.save()
        return Response(QuoteSerializer(quote).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def add_expense(self, request, pk=None):
        quote = self.get_object()
        description = request.data.get("description")
        quantity = request.data.get("quantity", 1)
        unit_price = request.data.get("unit_price")

        if not description or not unit_price:
            return Response(
                {"error": "Descrição e preço unitário são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quote_expense = QuoteExpense.objects.create(
            quote=quote,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
        )
        quote.save()
        return Response(QuoteSerializer(quote).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["delete"],
        url_path="remove_service/(?P<service_id>[^/.]+)",
    )
    def remove_service(self, request, pk=None, service_id=None):
        quote = self.get_object()
        try:
            quote_service = QuoteService.objects.get(id=service_id, quote=quote)
            quote_service.delete()
            quote.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except QuoteService.DoesNotExist:
            return Response(
                {"error": "Serviço não encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=True,
        methods=["delete"],
        url_path="remove_expense/(?P<expense_id>[^/.]+)",
    )
    def remove_expense(self, request, pk=None, expense_id=None):
        quote = self.get_object()
        try:
            quote_expense = QuoteExpense.objects.get(id=expense_id, quote=quote)
            quote_expense.delete()
            quote.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except QuoteExpense.DoesNotExist:
            return Response(
                {"error": "Despesa não encontrada"}, status=status.HTTP_404_NOT_FOUND
            )
