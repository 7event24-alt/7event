from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .serializers import AgendaViewSet

router = DefaultRouter()
router.register(r"agenda", AgendaViewSet, basename="agenda-api")

urlpatterns = [
    path("", include(router.urls)),
]
