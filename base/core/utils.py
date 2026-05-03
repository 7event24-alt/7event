from django.conf import settings
from django.contrib.sites.models import Site


def get_base_url(request=None):
    """Obtém URL base de forma segura e consistente.

    Prioriza:
    1. Django Sites framework (domain do Site)
    2. Variável de ambiente BASE_URL
    3. Domínio configurado em settings
    4. Request build_absolute_uri como fallback
    """
    try:
        site = Site.objects.first()
        if site and site.domain:
            domain = site.domain
            if not domain.startswith(('http://', 'https://')):
                domain = f"https://{domain}"
            return domain.rstrip('/')
    except Exception:
        pass

    base_url = getattr(settings, 'BASE_URL', None)
    if base_url:
        return base_url.rstrip('/')

    if request:
        return request.build_absolute_uri("/").rstrip("/")

    return getattr(settings, 'DEFAULT_BASE_URL', 'https://7event.com.br')


def build_url(path, request=None):
    """Constrói URL completa a partir de um path."""
    base = get_base_url(request)
    if path.startswith('/'):
        return f"{base}{path}"
    return f"{base}/{path}"