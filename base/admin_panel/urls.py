from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    admin_panel,
    account_detail,
    account_create,
    account_edit,
    account_delete,
    account_toggle_active,
    account_toggle_blocked,
    company_update_notifications,
    plan_list,
    plan_create,
    plan_edit,
    plan_delete,
    subscription_list,
)
from .api_views import AdminPanelViewSet

app_name = "admin_panel"

router = DefaultRouter()
router.register(r"metrics", AdminPanelViewSet, basename="admin-metrics-api")

urlpatterns = [
    path("", admin_panel, name="home"),
    path("contas/nova/", account_create, name="account_create"),
    path("contas/<int:pk>/", account_detail, name="account_detail"),
    path("contas/<int:pk>/editar/", account_edit, name="account_edit"),
    path("contas/<int:pk>/excluir/", account_delete, name="account_delete"),
    path(
        "contas/<int:pk>/toggle-active/",
        account_toggle_active,
        name="account_toggle_active",
    ),
    path(
        "contas/<int:pk>/toggle-blocked/",
        account_toggle_blocked,
        name="account_toggle_blocked",
    ),
    path(
        "contas/<int:pk>/notificacoes/",
        company_update_notifications,
        name="company_update_notifications",
    ),
    path("planos/", plan_list, name="plan_list"),
    path("planos/novo/", plan_create, name="plan_create"),
    path("planos/<int:pk>/editar/", plan_edit, name="plan_edit"),
    path("planos/<int:pk>/excluir/", plan_delete, name="plan_delete"),
    path("assinaturas/", subscription_list, name="subscription_list"),
    path("", include(router.urls)),
]

company_detail = account_detail
company_create = account_create
company_toggle_active = account_toggle_active
company_toggle_blocked = account_toggle_blocked
company_update_notifications = company_update_notifications
