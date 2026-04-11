from django.urls import path

from .views import (
    QuoteListView,
    QuoteCreateView,
    QuoteDetailView,
    QuoteUpdateView,
    QuoteDeleteView,
    QuoteAddServiceView,
    QuoteDeleteServiceView,
    QuoteAddExpenseView,
    QuoteDeleteExpenseView,
    QuotePDFView,
)

app_name = "quote"

urlpatterns = [
    path("", QuoteListView.as_view(), name="list"),
    path("novo/", QuoteCreateView.as_view(), name="create"),
    path("<int:pk>/", QuoteDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", QuoteUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", QuoteDeleteView.as_view(), name="delete"),
    path("<int:pk>/servico/novo/", QuoteAddServiceView.as_view(), name="add_service"),
    path(
        "<int:pk>/servico/<int:service_pk>/excluir/",
        QuoteDeleteServiceView.as_view(),
        name="delete_service",
    ),
    path("<int:pk>/despesa/nova/", QuoteAddExpenseView.as_view(), name="add_expense"),
    path(
        "<int:pk>/despesa/<int:expense_pk>/excluir/",
        QuoteDeleteExpenseView.as_view(),
        name="delete_expense",
    ),
    path("<int:pk>/pdf/", QuotePDFView.as_view(), name="pdf"),
]
