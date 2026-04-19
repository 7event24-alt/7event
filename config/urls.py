from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.cache import never_cache


@never_cache
def firebase_sw(request):
    import os
    sw_path = os.path.join(settings.BASE_DIR, "base", "static", "firebase-messaging-sw.js")
    with open(sw_path, "r") as f:
        return HttpResponse(f.read(), content_type="application/javascript")

@never_cache
def sw_js(request):
    import os
    sw_path = os.path.join(settings.BASE_DIR, "base", "static", "sw.js")
    with open(sw_path, "r") as f:
        return HttpResponse(f.read(), content_type="application/javascript")

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
    path("firebase-messaging-sw.js", firebase_sw, name="firebase-sw"),
    path("sw.js", sw_js, name="sw-js"),
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
    path("", include("base.landingpage.urls")),  # LP na raiz
    path("app/", include("base.dashboard.urls")),
    path("app/accounts/", include("base.accounts.urls")),
    path("app/planos/", include("base.plans.urls")),
    path("app/clientes/", include("base.clients.urls")),
    path("app/trabalhos/", include("base.jobs.urls")),
    path("app/despesas/", include("base.expenses.urls")),
    path("app/financeiro/", include("base.financial.urls")),
    path("app/agenda/", include("base.agenda.urls")),
    path("app/orcamentos/", include("base.quote.urls")),
    path("app/servicos/", include("base.services.urls")),
    path("app/admin-panel/", include("base.admin_panel.urls")),
    path("app/suporte/", include("base.support.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
