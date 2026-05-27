import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Version
VERSION = "1.5.1"

load_dotenv(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-dev-key-change-in-production"
)

# Auto-detect DEBUG based on environment
# - Local development: DEBUG=True
# - Production (AWS): DEBUG=False (unless explicitly set)
import socket

hostname = socket.gethostname()
is_production = hostname.startswith("ip-172") or hostname.startswith("ip-10")

# Check if DEBUG is explicitly set in environment
debug_from_env = os.environ.get("DEBUG", "").lower()

if debug_from_env in ["true", "1", "yes"]:
    DEBUG = True
elif debug_from_env in ["false", "0", "no"]:
    DEBUG = False
else:
    # Auto-detect: True locally, False in production
    DEBUG = not is_production

if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    allowed = os.environ.get("ALLOWED_HOSTS", "")
    if allowed:
        ALLOWED_HOSTS = [h.strip() for h in allowed.split(",") if h.strip()]
    else:
        # Default production hosts
        ALLOWED_HOSTS = ["7event.com.br", "www.7event.com.br", "localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_filters",
    "django_extensions",
    "base.core",
    "base.accounts",
    "base.dashboard",
    "base.clients",
    "base.jobs",
    "base.expenses",
    "base.financial",
    "base.agenda",
    "base.admin_panel",
    "base.quote",
    "base.services",
    "base.plans",
    "base.payments",
    "base.landingpage",
    "base.support",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "base.core.middleware.BlockedUserMiddleware",
    "base.core.middleware.AdminAccessMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

import socket

hostname = socket.gethostname()
is_production = hostname.startswith("ip-172") or hostname.startswith("ip-10")

if is_production and os.environ.get("DATABASE_URL"):
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(os.environ.get("DATABASE_URL"))}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "base.accounts.backends.PhoneEmailUsernameBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.hostinger.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 465))
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "True") == "True"
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "noreply@7event.com.br")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "7event <noreply@7event.com.br>"
)

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "base", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "base.core.context_processors.support_context",
                "base.core.context_processors.user_plan_context",
            ],
        },
    },
]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "base", "static")]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID = 1

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/app/accounts/login/"
LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/app/accounts/login/"

# Proxy/HTTPS settings (required for OAuth callbacks behind Nginx)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

GOOGLE_LOGIN_ENABLED = os.environ.get("GOOGLE_LOGIN_ENABLED", "false").lower() == "true"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()

ACCOUNT_LOGIN_METHODS = {"email", "username"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": GOOGLE_CLIENT_ID,
            "secret": GOOGLE_CLIENT_SECRET,
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKEND": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://7event.com.br",
    "https://www.7event.com.br",
]

SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # Temporário para permitir leitura via JavaScript
CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.app",
    "https://*.ngrok.io",
    "https://7event.com.br",
    "https://www.7event.com.br",
    "http://7event.com.br",
    "http://www.7event.com.br",
    "http://localhost",
    "http://127.0.0.1",
]

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://7event.com.br",
    "https://www.7event.com.br",
    "http://7event.com.br",
    "http://www.7event.com.br",
    "http://localhost",
    "http://127.0.0.1",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

JAZZMIN_SETTINGS = {
    "site_title": "7event - Admin",
    "site_header": "7event",
    "site_brand": "7event",
    "site_logo": "img/logo7event.png",
    "welcome_sign": "Bem-vindo ao painel administrativo",
    "copyright": "© 2025 7event - Sistema de Gestão de Eventos",
    "show_model_app_labels": True,
    "changeform_format": "horizontal_tab",
    "language_chooser": False,
    "navigation_expanded": True,
    "order_with_respect_to": [
        "accounts",
        "clients",
        "jobs",
        "expenses",
        "financial",
        "quote",
        "support",
    ],
    "icons": {
        "accounts.User": "fas fa-user",
        "accounts.Account": "fas fa-building",
        "accounts.Plan": "fas fa-layer-group",
        "accounts.Subscription": "fas fa-credit-card",
        "accounts.Notification": "fas fa-bell",
        "accounts.Feature": "fas fa-star",
        "clients.Client": "fas fa-handshake",
        "clients.ClientPhone": "fas fa-phone",
        "clients.ClientEmail": "fas fa-envelope",
        "jobs.Job": "fas fa-calendar-check",
        "expenses.Expense": "fas fa-receipt",
        "expenses.ExpenseCategory": "fas fa-tags",
        "quote.Quote": "fas fa-file-invoice-dollar",
        "quote.QuoteExpense": "fas fa-receipt",
        "services.Service": "fas fa-concierge-bell",
        "support.SupportMessage": "fas fa-headset",
        "agenda.Event": "fas fa-calendar-alt",
        "financial.Transaction": "fas fa-exchange-alt",
        "landingpage.LandingPageConfig": "fas fa-home",
    },
    "default_theme": "default",
    "dark_mode_theme": "darkly",
    "show_ui_builder": True,
    "user_avatar": "avatar",
    "default_icon_avatar": "fas fa-user",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_colour": "navbar-indigo-700",
    "accent_color": "accent-blue",
    "max_navbar_items": 25,
    "sidebar_small_text": False,
    "card_dark_mode": True,
}

# Custom error pages
handler400 = "base.core.error_views.bad_request"
handler403 = "base.core.error_views.permission_denied"
handler404 = "base.core.error_views.page_not_found"
handler500 = "base.core.error_views.server_error"

# Email for error reports
ERROR_REPORT_EMAIL = os.environ.get("ERROR_REPORT_EMAIL", "contato@7event.com.br")

# Mercado Pago
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
MP_PUBLIC_KEY = os.environ.get("MP_PUBLIC_KEY", "")
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET", "")
MP_NOTIFICATION_URL = os.environ.get("MP_NOTIFICATION_URL", "")
MP_TEST_PAYER_EMAIL = os.environ.get("MP_TEST_PAYER_EMAIL", "").strip()
MP_TEST_MODE = os.environ.get("MP_TEST_MODE", "false").lower() == "true"
MP_CURRENCY = os.environ.get("MP_CURRENCY", "BRL")
MP_BILLING_DUE_DAY = int(os.environ.get("MP_BILLING_DUE_DAY", "8"))
MP_BILLING_CUTOFF_DAY = int(os.environ.get("MP_BILLING_CUTOFF_DAY", "15"))
APP_PUBLIC_URL = os.environ.get("APP_PUBLIC_URL", "").strip().rstrip("/")
SUBSCRIPTIONS_RECURRING_ENABLED = os.environ.get("SUBSCRIPTIONS_RECURRING_ENABLED", "true").lower() == "true"
SUBSCRIPTIONS_ENFORCEMENT_ENABLED = os.environ.get("SUBSCRIPTIONS_ENFORCEMENT_ENABLED", "false").lower() == "true"
SUBSCRIPTIONS_CANCEL_AT_PERIOD_END_ENABLED = (
    os.environ.get("SUBSCRIPTIONS_CANCEL_AT_PERIOD_END_ENABLED", "true").lower() == "true"
)
SUBSCRIPTIONS_PAST_DUE_TOLERANCE_DAYS = int(os.environ.get("SUBSCRIPTIONS_PAST_DUE_TOLERANCE_DAYS", "5"))

# n8n webhooks (outbound)
N8N_WHATSAPP_WEBHOOK_URL = os.environ.get("N8N_WHATSAPP_WEBHOOK_URL", "").strip()
N8N_WHATSAPP_WEBHOOK_TOKEN = os.environ.get("N8N_WHATSAPP_WEBHOOK_TOKEN", "").strip()

# inbound webhook para disparar rotina de lembretes
TASK_REMINDERS_WEBHOOK_TOKEN = os.environ.get("TASK_REMINDERS_WEBHOOK_TOKEN", "").strip()
