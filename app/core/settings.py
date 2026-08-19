import string
from pathlib import Path
import os
from random import choice
from django.contrib import messages
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

# Secret Key
SECRET_KEY = os.environ.get('SECRET_KEY', ''.join(choice(string.ascii_lowercase) for i in range(32)))

# Debug Mode
DEBUG = bool(int(os.getenv("DEBUG", 0)))

# Allowed Hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "authentication",
    "expenses",
    "core",
    "income",
    "transfer",
    "contributor",
    "organization",
    "financial_reports",
    "attendance",
    'marriage',

    "wkhtmltopdf",
    "church_properties",
    "django_celery_beat",
    'cities_light',
    "anymail",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "authentication.middleware.Authorization",
]

# Database Configuration
DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_HOST'),
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'PORT': os.environ.get('DB_PORT', 5432),
        # 'OPTIONS': {
        #     'sslmode': 'require',
        # },
    }
}


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "contributor.context_processor.encode_logo",
                "contributor.context_processor.encode_signature"
            ],
        },
    },
]

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# Production settings
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    



    # EMAIL SETTING
    EMAIL_BACKEND = "anymail.backends.mailtrap.EmailBackend"
    ANYMAIL = {
    "MAILTRAP_API_TOKEN": os.environ.get("MAILTRAP_API_KEY"),
    }
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_PORT = os.environ.get("EMAIL_PORT")
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
    NATIONAL_OVERSEA_EMAIL = os.environ.get("NATIONAL_OVERSEA_EMAIL")


else:
    
    EMAIL_BACKEND = "anymail.backends.mailtrap.EmailBackend"
    ANYMAIL = {
      "MAILTRAP_API_TOKEN": os.environ.get("MAILTRAP_API_KEY"),
    }
        
    EMAIL_HOST = ""
    EMAIL_PORT =  587
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    DEFAULT_FROM_EMAIL = "info@example.com"
    NATIONAL_OVERSEA_EMAIL = "national@example.com"

# Locale
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Toronto"
USE_I18N = True
USE_TZ = True

# Authentication and Password Validation
AUTH_USER_MODEL = "authentication.User"
LOGIN_URL = "/authentication/login"
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

STATIC_URL = "static/"
MEDIA_URL = "/media/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "staticfiles")]

# Message Tags
MESSAGE_TAGS = {messages.ERROR: "danger"}

# Default Auto Field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# WSGI
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
    }
}

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_BEAT_SCHEDULE_FILENAME = 'celerybeat-schedule.db'
