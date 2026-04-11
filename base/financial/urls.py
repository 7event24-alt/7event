from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import financial
from .serializers import FinancialViewSet

app_name = "financial"

router = DefaultRouter()
router.register(r"api", FinancialViewSet, basename="financial-api")

urlpatterns = [
    path("", financial, name="home"),
    path("", include(router.urls)),
]
