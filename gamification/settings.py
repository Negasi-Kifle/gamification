"""
Django settings for gamification project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-m#ypnu_y8uxm)&hp#v#no0thi3ihi0%#^v@_ib!pryz=ljjir8",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = (
    os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if os.environ.get("DJANGO_ALLOWED_HOSTS")
    else []
)


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_migration_linter",
    # Module apps - register Infrastructure layers
    "bonus.src.Infrastructure",
]

MIDDLEWARE = [
    # Correlation ID middleware - must be first to capture all logs
    "shared.middleware.CorrelationIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gamification.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gamification.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("DB_NAME", "gamification"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Service name for structured logs
SERVICE_NAME = os.environ.get("SERVICE_NAME", "gamification")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "shared.logging.formatter.JsonFormatter",
        },
        "verbose": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "console_verbose": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "bonus": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "shared": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}


# =============================================================================
# Kafka Configuration
# =============================================================================
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SCHEMA_REGISTRY_URL = os.environ.get("SCHEMA_REGISTRY_URL", "http://localhost:8081")
AUDIT_LOGS_TOPIC = os.environ.get("AUDIT_LOGS_TOPIC", "audit-logs")
EXCEPTION_LOGS_TOPIC = os.environ.get("EXCEPTION_LOGS_TOPIC", "exception-logs")


# =============================================================================
# Scheduler Configuration
# =============================================================================
SCHEDULER_SERVICE_URL = os.environ.get("SCHEDULER_SERVICE_URL", "localhost:50052")


# =============================================================================
# OpenTelemetry / Tracing Configuration (per tech requirements)
# =============================================================================
OTEL_ENABLED = os.environ.get("OTEL_ENABLED", "false").lower() in ("true", "1", "yes")
JAEGER_ENDPOINT = os.environ.get("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
OTEL_SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", SERVICE_NAME)
OTEL_SERVICE_VERSION = os.environ.get("OTEL_SERVICE_VERSION", "0.1.0")

# Initialize tracing at startup (if enabled)
if OTEL_ENABLED:
    try:
        from shared.tracing import init_tracing

        init_tracing(
            service_name=OTEL_SERVICE_NAME,
            service_version=OTEL_SERVICE_VERSION,
            jaeger_endpoint=JAEGER_ENDPOINT,
            enabled=True,
        )
    except ImportError:
        pass  # OpenTelemetry packages not installed
