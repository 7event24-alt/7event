from django.urls import path
from django.views.generic import TemplateView, RedirectView

from .views import (
    SupportContactView,
    SupportSuccessView,
    SupportAdminListView,
    SupportAdminDetailView,
)

app_name = "support"

urlpatterns = [
    path("", SupportContactView.as_view(), name="contact"),
    path("sucesso/", SupportSuccessView.as_view(), name="success"),
    path("faq/", RedirectView.as_view(url="/", permanent=False), name="faq"),
    path("admin/", SupportAdminListView.as_view(), name="admin_list"),
    path("admin/<int:pk>/", SupportAdminDetailView.as_view(), name="admin_detail"),
]
