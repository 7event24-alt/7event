from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ServiceViewSet

router = DefaultRouter()
router.register(r"services", ServiceViewSet, basename="service-api")

urlpatterns = [
    path("", include(router.urls)),
]
