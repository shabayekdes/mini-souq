"""
Django settings for the MiniSouq project.

All environment-specific values are read from environment variables (or a
local, untracked `.env` file via python-decouple). See `.env.example` and the
README for the full reference.

Production is the default: unless DJANGO_DEBUG is explicitly enabled, the
project requires DJANGO_SECRET_KEY and DATABASE_URL and turns on HTTPS-only
cookies and redirects.
"""

import sys
from pathlib import Path

import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false."
        )
    # Development-only fallback; never used when DEBUG is off.
    SECRET_KEY = "django-insecure-local-development-only-key"

# Hosts / origins. On Railway, the generated public domain is picked up
# automatically from RAILWAY_PUBLIC_DOMAIN; custom domains must be listed
# explicitly in DJANGO_ALLOWED_HOSTS and DJANGO_CSRF_TRUSTED_ORIGINS.
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("DJANGO_CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

RAILWAY_PUBLIC_DOMAIN = config("RAILWAY_PUBLIC_DOMAIN", default="")
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")

if DEBUG:
    ALLOWED_HOSTS += ["127.0.0.1", "localhost"]
    CSRF_TRUSTED_ORIGINS += ["http://127.0.0.1:8000", "http://localhost:8000"]


# HTTPS / security headers
# Railway (and most PaaS platforms) terminate TLS at the edge proxy and forward
# the original scheme in X-Forwarded-Proto. Only trust that header when the app
# is reachable exclusively through such a proxy.
if config("DJANGO_TRUST_X_FORWARDED_PROTO", default=not DEBUG, cast=bool):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG, cast=bool)
SESSION_COOKIE_SECURE = config("DJANGO_SECURE_COOKIES", default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
# HSTS is opt-in: once a browser has seen it, plain HTTP is refused for the
# whole duration. Start small (e.g. 3600) and increase after verifying HTTPS.
SECURE_HSTS_SECONDS = config("DJANGO_SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool
)
SECURE_HSTS_PRELOAD = config("DJANGO_SECURE_HSTS_PRELOAD", default=False, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# Email config
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)  # port 587
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)  # port 465
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER or "webmaster@localhost"
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

ADMIN_USER_NAME = config("ADMIN_USER_NAME", default="Admin user")
ADMIN_USER_EMAIL = config("ADMIN_USER_EMAIL", default="")

# 500 errors are emailed to these users
ADMINS = [(ADMIN_USER_NAME, ADMIN_USER_EMAIL)] if ADMIN_USER_EMAIL else []
MANAGERS = ADMINS


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'core.apps.CoreStaticFilesConfig',  # django.contrib.staticfiles
    # My Apps
    'product',
    'store',
    'checkout',
    # third-party-apps
    "allauth_ui",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
    "widget_tweaks",
    'slippers'
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "checkout.context_processors.cart_count",
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
#
# DATABASE_URL is required in production. In development (DJANGO_DEBUG=1) an
# unset DATABASE_URL falls back to a local SQLite file.

DATABASE_URL = config("DATABASE_URL", default="")
CONN_MAX_AGE = config("CONN_MAX_AGE", default=300, cast=int)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=CONN_MAX_AGE,
            conn_health_checks=True,
            ssl_require=config("DATABASE_SSL_REQUIRE", default=False, cast=bool),
        )
    }
elif DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    raise ImproperlyConfigured("DATABASE_URL must be set when DJANGO_DEBUG is false.")


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Django Allauth Config
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
# "none" | "optional" | "mandatory". "mandatory" requires working SMTP settings.
ACCOUNT_EMAIL_VERIFICATION = config("ACCOUNT_EMAIL_VERIFICATION", default="none")
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[MI] "
ALLAUTH_UI_THEME = "light"

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]

# GitHub OAuth credentials are stored as a SocialApp in the admin (or via the
# APP setting), never in source control. The provider reports which GitHub
# e-mail addresses are verified, so we don't force VERIFIED_EMAIL=True.
SOCIALACCOUNT_PROVIDERS = {
    "github": {}
}

# allauth_ui ships its slippers components.yaml inside its own app template
# directory; this check only looks in TEMPLATES["DIRS"]. The login/signup
# pages are covered by tests to make sure the components still resolve.
SILENCED_SYSTEM_CHECKS = ["slippers.E001"]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_BASE_DIR = BASE_DIR / "staticfiles"
STATICFILES_VENDOR_DIR = STATICFILES_BASE_DIR / "vendors"

# source(s) for python manage.py collectstatic
STATICFILES_DIRS = [
    STATICFILES_BASE_DIR
]

# output for python manage.py collectstatic
# local cdn
STATIC_ROOT = BASE_DIR / "local-cdn"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # The manifest only exists after collectstatic, so tests use plain storage.
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Logging: send errors to stderr so they show up in container/Railway logs.
# Django's default config only logs to the console when DEBUG is on.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {
            "handlers": ["console", "mail_admins"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        # Host-header scans are routine on public hosts; log them, don't email.
        "django.security.DisallowedHost": {
            "handlers": ["console"],
            "propagate": False,
        },
    },
}


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
