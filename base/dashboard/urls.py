from django.urls import path
from .views import dashboard, search

app_name = "dashboard"

urlpatterns = [
    path("", dashboard, name="home"),
    path("buscar/", search, name="search"),
    path("search/", search, name="search_alias"),
]
