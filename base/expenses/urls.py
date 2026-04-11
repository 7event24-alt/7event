from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ExpenseViewSet
from .views import (
    ExpenseListView,
    ExpenseCreateView,
    ExpenseUpdateView,
    ExpenseDeleteView,
)

app_name = "expenses"

router = DefaultRouter()
router.register(r"", ExpenseViewSet, basename="expense-api")

urlpatterns = [
    path("", ExpenseListView.as_view(), name="list"),
    path("nova/", ExpenseCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", ExpenseUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", ExpenseDeleteView.as_view(), name="delete"),
    path("api/", include(router.urls)),
]
