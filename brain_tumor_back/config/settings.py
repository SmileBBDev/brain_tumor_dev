import environ
import os
from pathlib import Path
from datetime import timedelta
from .base import * # 공통 설정
from corsheaders.defaults import default_headers
from dotenv import load_dotenv
load_dotenv()


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
    "rest_framework",
    "drf_spectacular",
    # 기존 시스템 앱들 (유지)
    "apps.accounts",        # 사용자 관리
    "apps.audit",           # 감사 로그
    "apps.authorization",   # 인증/권한 (로그인 시스템)
    "apps.common",          # 공통 모델
    "apps.menus",           # 메뉴 관리
    # CDSS 앱들
    "apps.patients",        # 환자 관리
    "apps.encounters",      # 진료 관리
    # "apps.scripts",         # 스크립트
    # # 새로운 권한별 앱들
    # "apps.doctor",          # 의사용 앱
    # "apps.nurse",           # 간호사용 앱
    # "apps.patient",         # 환자용 앱
    # "apps.radiologist",     # 영상의학과용 앱
    # "apps.lab_tech",        # 검사실용 앱
    # "apps.admin_clinical",  # 관리자용 앱
    # "apps.external",        # 외부 연동용 앱
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

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul"

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


# Swagger 설정
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),

}

SPECTACULAR_SETTINGS = {
    "TITLE": "NeuroNova CDSS API",
    "DESCRIPTION": "Clinical Decision Support System API",
    "VERSION": "1.0.0",
    "USE_SESSION_AUTH": False,
    "SERVE_INCLUDE_SCHEMA": False,  # 문서 로드시 자동 호출 방지
    "SECURITY_SCHEMES": {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
    },
}


# 보안 기능 활성화 여부 (True/False)
ENABLE_SECURITY = True  # 운영 환경
# ENABLE_SECURITY = False  # 개발 환경

# 이메일 발송
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = f"BrainTumor System <{EMAIL_HOST_USER}>"
