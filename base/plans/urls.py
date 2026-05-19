from django.urls import path
from . import views

app_name = "plans"

urlpatterns = [
    path("", views.plan_list, name="list"),
    path("ativar-free/", views.activate_free, name="activate_free"),
    path("aguardo/", views.waiting_confirmation, name="waiting"),
    path("pagamento/sucesso/", views.payment_success, name="payment_success"),
    path("pagamento/pendente/", views.payment_pending, name="payment_pending"),
    path("pagamento/falha/", views.payment_failure, name="payment_failure"),
]
