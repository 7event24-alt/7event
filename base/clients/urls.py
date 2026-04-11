from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ClientViewSet
from .views import (
    ClientListView,
    ClientCreateView,
    ClientUpdateView,
    ClientDetailView,
    ClientDeleteView,
    ClientQuickCreateView,
)

app_name = "clients"

router = DefaultRouter()
router.register(r"", ClientViewSet, basename="client-api")

urlpatterns = [
    path("", ClientListView.as_view(), name="list"),
    path("novo/", ClientCreateView.as_view(), name="create"),
    path("rapido/", ClientQuickCreateView.as_view(), name="quick_create"),
    path("<int:pk>/", ClientDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", ClientUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", ClientDeleteView.as_view(), name="delete"),
    path("api/", include(router.urls)),
]
