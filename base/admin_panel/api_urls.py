from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AdminPanelViewSet

router = DefaultRouter()
router.register(r"metrics", AdminPanelViewSet, basename="admin-metrics-api")

urlpatterns = [
    path("", include(router.urls)),
]
