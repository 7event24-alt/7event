from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import agenda, day_detail
from .serializers import AgendaViewSet, AgendaEventsView
from base.admin_panel.views import admin_panel as admin_panel_view

app_name = "agenda"

router = DefaultRouter()
router.register(r"api", AgendaViewSet, basename="agenda-api")

urlpatterns = [
    path("", agenda, name="home"),
    path("dia/<int:year>/<int:month>/<int:day>/", day_detail, name="day_detail"),
    path("", include(router.urls)),
    path("api/eventos/", AgendaEventsView.as_view(), name="agenda-events"),
]
