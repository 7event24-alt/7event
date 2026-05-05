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
    user_create,
    user_edit,
    user_delete,
    user_upgrade_plan,
)
from .api_views import AdminPanelViewSet

app_name = "admin_panel"

router = DefaultRouter()
router.register(r"metrics", AdminPanelViewSet, basename="admin-metrics-api")

urlpatterns = [
    path("", admin_panel, name="home"),
    path("usuarios/", user_list, name="user_list"),
    path("usuarios/novo/", user_create, name="user_create"),
    path("usuarios/<int:pk>/", user_detail, name="user_detail"),
    path("usuarios/<int:pk>/editar/", user_edit, name="user_edit"),
    path("usuarios/<int:pk>/excluir/", user_delete, name="user_delete"),
    path("usuarios/<int:pk>/upgrade-plano/", user_upgrade_plan, name="user_upgrade_plan"),
    path("planos/", plan_list, name="plan_list"),
    path("planos/novo/", plan_create, name="plan_create"),
    path("planos/<int:pk>/editar/", plan_edit, name="plan_edit"),
    path("planos/<int:pk>/excluir/", plan_delete, name="plan_delete"),
    path("assinaturas/", subscription_list, name="subscription_list"),
    path("", include(router.urls)),
]
