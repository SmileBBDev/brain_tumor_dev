import environ
import os
from pathlib import Path
from datetime import timedelta
from .base import * # 공통 설정
from corsheaders.defaults import default_headers


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# env 초기화
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, 'dbconn.env'))  # 여기서 파일명 변경


SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = ["127.0.0.1", "localhost"] 
# ALLOWED_HOSTS = [] # 운영 시 실제 도메인 입력

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "corsheaders",
    "channels",
    "apps.accounts",
    "apps.audit",
    "apps.authorization",
    "apps.common",
    "apps.menus",

]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # 반드시 CommonMiddleware보다 위에
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]



# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# 데이터베이스 설정
DATABASES = {
    # MYSQL_DB 설정
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('MYSQL_DB'),
        'USER': env('MYSQL_USER'),
        'PASSWORD': env('MYSQL_PASSWORD'),
        'HOST': env('MYSQL_HOST'),
        'PORT': env('MYSQL_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    },

}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DB와 연결된 로그인 정보 호출
AUTH_USER_MODEL = "accounts.User"

# 로그인 로직 (있어야만 로그인 처리 가능)
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.LoginBackend",
]

# SimpleJWT 설정
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME" : timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME" : timedelta(days=1),
    "AUTH_HEADER_TYPES" : ("Bearer",),
}

# CORS 옵션 추가
# 허용할 오리진 지정
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite 개발 서버
    "http://127.0.0.1:5173",   # Vite 개발 서버

    # "https://example.com",   # 운영 프론트엔드
]

# 헤더 허용 (Authorization 등) : default_headers(기본 헤더) +  Authorization 추가
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
]
# 쿠키를 포함한 cross-origin 요청
CORS_ALLOW_CREDENTIALS = True
