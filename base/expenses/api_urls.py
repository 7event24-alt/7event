from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ExpenseViewSet

router = DefaultRouter()
router.register(r"expenses", ExpenseViewSet, basename="expense-api")

urlpatterns = [
    path("", include(router.urls)),
]
