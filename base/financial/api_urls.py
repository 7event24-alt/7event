from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .serializers import FinancialViewSet

router = DefaultRouter()
router.register(r"financial", FinancialViewSet, basename="financial-api")

urlpatterns = [
    path("", include(router.urls)),
]
