from django.urls import path
from . import views

app_name = "plans"

urlpatterns = [
    path("", views.plan_list, name="list"),
    path("ativar-free/", views.activate_free, name="activate_free"),
    path("aguardo/", views.waiting_confirmation, name="waiting"),
]
