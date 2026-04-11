from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import JobViewSet

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job-api")

urlpatterns = [
    path("", include(router.urls)),
]
