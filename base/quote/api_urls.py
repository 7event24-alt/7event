from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import QuoteViewSet

router = DefaultRouter()
router.register(r"quotes", QuoteViewSet, basename="quote-api")

urlpatterns = [
    path("", include(router.urls)),
]
