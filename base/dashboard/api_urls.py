from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r"dashboard", api_views.DashboardViewSet, basename="dashboard-api")

urlpatterns = [
    path("", include(router.urls)),
    path("stats/", api_views.dashboard_api, name="dashboard-stats"),
]
