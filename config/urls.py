from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Custom error handlers
from base.core.error_views import (
    bad_request,
    permission_denied,
    page_not_found,
    server_error,
)

handler400 = bad_request
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("base.accounts.api_urls")),
    path("api/v1/", include("base.clients.api_urls")),
    path("api/v1/", include("base.jobs.api_urls")),
    path("api/v1/", include("base.expenses.api_urls")),
    path("api/v1/", include("base.financial.api_urls")),
    path("api/v1/", include("base.agenda.api_urls")),
    path("api/v1/", include("base.admin_panel.api_urls")),
    path("api/v1/", include("base.quote.api_urls")),
    path("api/v1/", include("base.services.api_urls")),
    path("api/v1/", include("base.dashboard.api_urls")),
    path("auth/", include("django.contrib.auth.urls")),
    path("accounts/", include("base.accounts.urls")),
    path("planos/", include("base.plans.urls")),
    path("landingpage/", include("base.landingpage.urls")),
    path("", include("base.dashboard.urls")),
    path("clientes/", include("base.clients.urls")),
    path("trabalhos/", include("base.jobs.urls")),
    path("despesas/", include("base.expenses.urls")),
    path("financeiro/", include("base.financial.urls")),
    path("agenda/", include("base.agenda.urls")),
    path("orcamentos/", include("base.quote.urls")),
    path("servicos/", include("base.services.urls")),
    path("admin-panel/", include("base.admin_panel.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
