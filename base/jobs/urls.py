from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import JobViewSet
from .views import (
    JobListView,
    JobCreateView,
    JobUpdateView,
    JobDetailView,
    JobDeleteView,
    JobDuplicateView,
    JobConfirmView,
    JobCompleteView,
    JobCancelView,
    JobApproveView,
    JobConfirmPaymentView,
    JobConfirmPartialPaymentView,
    JobConfirmRemainingPaymentView,
    JobTeamPDFView,
    JobAddStaffView,
    JobUpdateStaffView,
    JobRemoveStaffView,
    JobStaffStatusUpdateView,
    ProfessionalSearchView,
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
    path("<int:pk>/duplicar/", JobDuplicateView.as_view(), name="duplicate"),
    path("<int:pk>/confirmar/", JobConfirmView.as_view(), name="confirm"),
    path("<int:pk>/concluir/", JobCompleteView.as_view(), name="complete"),
    path("<int:pk>/cancelar/", JobCancelView.as_view(), name="cancel"),
    path("<int:pk>/aprovar/", JobApproveView.as_view(), name="approve"),
    path("<int:pk>/confirmar-pagamento/", JobConfirmPaymentView.as_view(), name="confirm_payment"),
    path("<int:pk>/confirmar-parcela/", JobConfirmPartialPaymentView.as_view(), name="confirm_partial"),
    path("<int:pk>/confirmar-restante/", JobConfirmRemainingPaymentView.as_view(), name="confirm_remaining"),
    path("<int:pk>/equipe-pdf/", JobTeamPDFView.as_view(), name="team_pdf"),
    path("<int:pk>/adicionar-staff/", JobAddStaffView.as_view(), name="add_staff"),
    path("<int:pk>/staff/<int:staff_pk>/atualizar/", JobUpdateStaffView.as_view(), name="update_staff"),
    path("<int:pk>/staff/<int:staff_pk>/remover/", JobRemoveStaffView.as_view(), name="remove_staff"),
    path("<int:pk>/staff/<int:staff_pk>/status/", JobStaffStatusUpdateView.as_view(), name="update_staff_status"),
    path("buscar-profissionais/", ProfessionalSearchView.as_view(), name="search_professionals"),
    path("api/", include(router.urls)),
]
