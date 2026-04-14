from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import JobViewSet
from .views import (
    JobListView,
    JobCreateView,
    JobUpdateView,
    JobDetailView,
    JobDeleteView,
    JobConfirmView,
    JobCompleteView,
    JobCancelView,
    JobApproveView,
)

app_name = "jobs"

router = DefaultRouter()
router.register(r"", JobViewSet, basename="job-api")

urlpatterns = [
    path("", JobListView.as_view(), name="list"),
    path("novo/", JobCreateView.as_view(), name="create"),
    path("<int:pk>/", JobDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", JobUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", JobDeleteView.as_view(), name="delete"),
    path("<int:pk>/confirmar/", JobConfirmView.as_view(), name="confirm"),
    path("<int:pk>/concluir/", JobCompleteView.as_view(), name="complete"),
    path("<int:pk>/cancelar/", JobCancelView.as_view(), name="cancel"),
    path("<int:pk>/aprovar/", JobApproveView.as_view(), name="approve"),
    path("api/", include(router.urls)),
]
