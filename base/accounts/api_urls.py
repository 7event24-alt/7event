from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_auth

router = DefaultRouter()
router.register(r"auth", api_auth.AuthViewSet, basename="auth-api")
router.register(r"users", api_auth.AuthViewSet, basename="users-api")

urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
