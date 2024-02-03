import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "backend.apps.BackendConfig",
    "djoser",
    "drf_spectacular",
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

ROOT_URLCONF = "retail_order_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
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

WSGI_APPLICATION = "retail_order_api.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
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

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "ru-RU"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'backend.CustomUser'

REST_FRAMEWORK = {
    # Разрешения
    # 'DEFAULT_PERMISSION_CLASSES': [
    #     'rest_framework.permissions.IsAuthenticated',
    #     'rest_framework.permissions.AllowAny',
    #     'rest_framework.permissions.IsAuthenticated'
    # ],

    # Дросселирование запросов
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/hour',
        'user': '100/hour'
    },

    # Классы рендеринга
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],

    # Классы аутентификации
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),

    # Генерация схем OpenAPI
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# SMTP
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_TLS = os.getenv("DEBUG").lower() == "true"

# Djoser
DJOSER = {
    'SEND_ACTIVATION_EMAIL': True,  # Подтв-ие email после регистрации и ред-ии email
    'ACTIVATION_URL': '#/activate/{uid}/{token}',  # URL для активации (uid, token)
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,  # Подтв-ие email после смены пароля
    'USER_CREATE_PASSWORD_RETYPE': True,  # Подтв-ие пароля при создании (передать re_password)
    'SET_PASSWORD_RETYPE': True,  # Подтв-ие пароля при смене (передать re_new_password)
    'PASSWORD_RESET_CONFIRM_RETYPE': True,  # Подтв-ие пароля при сбросе
    'PASSWORD_RESET_CONFIRM_URL': '#/password-reset/{uid}/{token}',  # URL подтв-ие сброса пароля
    'LOGOUT_ON_PASSWORD_CHANGE': True,  # Выход при смене пароля
    'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': True,  # Ошибка 400 при сбросе, если email не существует
}

# drf_spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "retail-order-api",
    "DESCRIPTION": "API Сервис заказа товаров для розничных сетей",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Celery
CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "redis://localhost:6379"

if DEBUG:
    # debug_toolbar
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware',
                   ]
    INSTALLED_APPS += ['debug_toolbar']
    INTERNAL_IPS = ['127.0.0.1']



# django-allauth
# AUTHENTICATION_BACKENDS += [
#     "django.contrib.auth.backends.ModelBackend",
#     "allauth.account.auth_backends.AuthenticationBackend",
# ]
# INSTALLED_APPS += [
#     "allauth",
#     "allauth.account",
#     "allauth.socialaccount",
#     'allauth.socialaccount.providers.google',
# ]
# MIDDLEWARE += [
#     "allauth.account.middleware.AccountMiddleware",  # django-allauth
# ]
# SOCIALACCOUNT_PROVIDERS = {
#     "google": {
#         'APP': {
#             "client_id": os.getenv("ALLAUTH_GOOGLE_CLIENT_ID"),
#             "secret": os.getenv("ALLAUTH_GOOGLE_SECRET"),
#             "key": ""
#         },
#         "SCOPE": [
#             "profile",
#             "email",
#         ],
#         "AUTH_PARAMS": {
#             "access_type": "online",
#         },
#
#     }
# }
# django-allauth
# SITE_ID = 1
# ACCOUNT_AUTHENTICATION_METHOD = "email"
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# ACCOUNT_USERNAME_REQUIRED = False
# ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# LOGIN_REDIRECT_URL = '/'
# LOGOUT_REDIRECT_URL = '/'