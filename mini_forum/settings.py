# mini_forum/mini_forum/settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-change-me"
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1", "localhost",
    ".ngrok-free.dev",
    "prorestoration-katheryn-unjumpable.ngrok-free.dev",
]

INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # allauth ต้องมี
    "django.contrib.sites",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",

    # providers
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",

    # apps ของโปรเจกต์
    "accounts",
    "forum",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # ✅ allauth 0.63+ ต้องมี
    "allauth.account.middleware.AccountMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mini_forum.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # << override templates ของ allauth
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # << จำเป็นสำหรับ allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mini_forum.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
  "default": {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": "redis://127.0.0.1:6379/1",
    "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
  }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True

# Static & Media
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- allauth redirects ---
LOGIN_URL = "account_login"           # ใช้ของ allauth
LOGIN_REDIRECT_URL = "forum:home"
LOGOUT_REDIRECT_URL = "forum:home"
ACCOUNT_LOGOUT_REDIRECT_URL = LOGOUT_REDIRECT_URL

# allauth backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# allauth options
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"

# ให้ logout เฉพาะแบบ POST (ปลอดภัยกว่า)
ACCOUNT_LOGOUT_ON_GET = False

# Providers
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}


# Password hashers
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# ---------------- Email (Gmail SMTP with App Password) ----------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = "bfirstkok@gmail.com"      # บัญชี Gmail ที่สร้าง App Password
EMAIL_HOST_PASSWORD = "evuwphdqtwaaneob"     # App Password 16 ตัว (ไม่มีช่องว่าง)
DEFAULT_FROM_EMAIL = "Mini Forum <bfirstkok@gmail.com>"

# ให้ลิงก์ในอีเมลและ allauth ใช้ https (เวลาเปิดผ่าน ngrok)
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ngrok / https
CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.dev",
    "https://prorestoration-katheryn-unjumpable.ngrok-free.dev",
]
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# dev convenience
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
