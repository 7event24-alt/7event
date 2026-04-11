from django.urls import path

from .views import (
    ServiceListView,
    ServiceCreateView,
    ServiceUpdateView,
    ServiceDeleteView,
)

app_name = "services"

urlpatterns = [
    path("", ServiceListView.as_view(), name="list"),
    path("novo/", ServiceCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", ServiceUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", ServiceDeleteView.as_view(), name="delete"),
]
