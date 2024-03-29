import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env.str("SECRET_KEY", "")
DEBUG = env.bool("DEBUG", True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "baton",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "backend.apps.BackendConfig",
    "djoser",
    "social_django",  # djoser social auth
    "rest_framework_simplejwt",
    "drf_spectacular",
    "imagekit",
    "baton.autodiscover",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


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
                # djoser social auth
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "retail_order_api.wsgi.application"
ROOT_URLCONF = "retail_order_api.urls"
DATABASES = {
    "default": {
        "ENGINE": env.str("POSTGRES_ENGINE", "django.db.backends.sqlite3"),
        "NAME": env.str("POSTGRES_DB", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": env.str("POSTGRES_USER", "user"),
        "PASSWORD": env.str("POSTGRES_PASSWORD", "password"),
        "HOST": env.str("POSTGRES_HOST", "localhost"),
        "PORT": env.str("POSTGRES_PORT", "5432"),
    }
}

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


LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    # Дросселирование запросов
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "10/hour", "user": "100/hour"},
    # Классы рендеринга
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    # Классы аутентификации
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Генерация схем OpenAPI
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Формат для тестов
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}


# SMTP
EMAIL_BACKEND = env.str("EMAIL_BACKEND", "")
EMAIL_HOST = env.str("EMAIL_HOST", "")
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "")
EMAIL_PORT = env.str("EMAIL_PORT", "")
EMAIL_USE_TLS = env.str("EMAIL_USE_TLS", "")


# Djoser
DJOSER = {
    "TOKEN_MODEL": None,
    "SEND_ACTIVATION_EMAIL": True,  # Подтв-ие email после регистрации и ред-ии email
    "ACTIVATION_URL": "#/activate/{uid}/{token}",  # URL для активации (uid, token)
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,  # Подтв-ие email после смены пароля
    "USER_CREATE_PASSWORD_RETYPE": True,  # Подтв-ие пароля при создании (передать re_password)
    "SET_PASSWORD_RETYPE": True,  # Подтв-ие пароля при смене (передать re_new_password)
    "PASSWORD_RESET_CONFIRM_RETYPE": True,  # Подтв-ие пароля при сбросе
    "PASSWORD_RESET_CONFIRM_URL": "#/password-reset/{uid}/{token}",  # URL подтв-ие сброса пароля
    "LOGOUT_ON_PASSWORD_CHANGE": True,  # Выход при смене пароля
    "PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND": True,  # Ошибка 400 при сбросе, если email не существует
    # djoser social auth
    "LOGIN_FIELD": "email",
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": [
        "http://127.0.0.1:8000/api/v1/auth/social/redirect/"
    ],
}

# djoser social auth
AUTH_USER_MODEL = "backend.CustomUser"
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "backend.utils.custom_get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)


# Google OAuth2
SOCIAL_AUTH_USER_MODEL = "backend.CustomUser"
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")

# Github OAuth2
SOCIAL_AUTH_GITHUB_KEY = env.str("SOCIAL_AUTH_GITHUB_KEY", "")
SOCIAL_AUTH_GITHUB_SECRET = env.str("SOCIAL_AUTH_GITHUB_SECRET", "")
SOCIAL_AUTH_GITHUB_SCOPE = ["read:user", "user:email"]

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.github.GithubOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)


# simplejwt
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=6000),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=20),
    "AUTH_HEADER_TYPES": ("JWT",),
}

# drf_spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "retail-order-api",
    "DESCRIPTION": "API Сервис заказа товаров для розничных сетей",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Celery
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", "redis://localhost:6379")
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", "redis://localhost:6379")

# django-baton
BATON = {
    "SITE_HEADER": "retail-order-api",
    "SITE_TITLE": "Административная панель",
    "INDEX_TITLE": "Главная",
    "SUPPORT_HREF": "https://github.com/Edmaroff",
    "COPYRIGHT": "Copyright © 2024",
    "POWERED_BY": '<a href="https://github.com/Edmaroff">Edmaroff</a>',
    "CHANGELIST_FILTERS_IN_MODAL": True,
    "CHANGELIST_FILTERS_FORM": True,
    "MENU_TITLE": "Menu",
    "GRAVATAR_ENABLED": True,
    "GRAVATAR_DEFAULT_IMG": "mp",
    "MENU": (
        {"type": "title", "label": "Основное", "apps": ("auth",)},
        {
            "type": "app",
            "name": "auth",
            "label": "Authentication",
            "models": ({"name": "group", "label": "Groups"},),
        },
        {
            "type": "app",
            "name": "social_django",
            "label": "Social Django",
        },
        {
            "type": "app",
            "name": "backend",
            "label": "Управление пользователями",
            "models": (
                {"name": "customuser", "label": "Пользователи"},
                {"name": "contact", "label": "Контакты"},
            ),
        },
        {
            "type": "app",
            "name": "backend",
            "label": "Управление магазинами",
            "models": ({"name": "shop", "label": "Магазины"},),
        },
        {
            "type": "app",
            "name": "backend",
            "label": "Управление продуктами",
            "models": (
                {"name": "category", "label": "Категории"},
                {"name": "product", "label": "Продукты"},
                {"name": "productinfo", "label": "Информация о продуктах"},
                {"name": "parameter", "label": "Общие параметры"},
                {"name": "productparameter", "label": "Параметры продукта"},
            ),
        },
        {
            "type": "app",
            "name": "backend",
            "label": "Управление заказами",
            "models": ({"name": "order", "label": "Заказы"},),
        },
        {
            "type": "free",
            "label": "Документация API",
            "url": "http://localhost:8000/api/v1/schema/docs/",
        },
        {
            "type": "free",
            "label": "Документация Postman",
            "url": "https://documenter.getpostman.com/view/25907870/2s9Ykn92Za",
        },
    ),
}

# django-imagekit
IMAGEKIT_CACHEFILE_DIR = (
    "CACHE"  # Каталог, в который будут кэшироваться файлы изображений
)
IMAGEKIT_SPEC_CACHEFILE_NAMER = (
    "backend.utils.custom_source_name_as_path"  # Генерация пути производных файлов
)

# Константы backend
STATE_CHOICES = (
    ("basket", "Статус корзины"),
    ("new", "Новый"),
    ("confirmed", "Подтвержден"),
    ("assembled", "Собран"),
    ("sent", "Отправлен"),
    ("delivered", "Доставлен"),
    ("canceled", "Отменен"),
)
USER_TYPE_CHOICES = (
    ("shop", "Магазин"),
    ("buyer", "Покупатель"),
)
DEFAULT_QUANTITY_ORDER_ITEM = 1
MIN_QUANTITY_ORDER_ITEM = 1
MAX_QUANTITY_ORDER_ITEM = 100
DEFAULT_PATH_PRODUCT_IMAGE = "default_images/products/default_image.jpg"
WHITELISTED_IMAGE_TYPES = {
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
}
IMAGE_MAX_SIZE_MB = 3

if DEBUG:
    # debug_toolbar
    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    INSTALLED_APPS += ["debug_toolbar"]
    INTERNAL_IPS = ["127.0.0.1"]
