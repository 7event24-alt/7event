from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    admin_panel,
    plan_list,
    plan_create,
    plan_edit,
    plan_delete,
    subscription_list,
    user_list,
    user_detail,
)
from .api_views import AdminPanelViewSet

app_name = "admin_panel"

router = DefaultRouter()
router.register(r"metrics", AdminPanelViewSet, basename="admin-metrics-api")

urlpatterns = [
    path("", admin_panel, name="home"),
    path("usuarios/", user_list, name="user_list"),
    path("usuarios/<int:pk>/", user_detail, name="user_detail"),
    path("planos/", plan_list, name="plan_list"),
    path("planos/novo/", plan_create, name="plan_create"),
    path("planos/<int:pk>/editar/", plan_edit, name="plan_edit"),
    path("planos/<int:pk>/excluir/", plan_delete, name="plan_delete"),
    path("assinaturas/", subscription_list, name="subscription_list"),
    path("", include(router.urls)),
]