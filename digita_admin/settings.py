import os
from pathlib import Path
from datetime import timedelta

# Build paths didalam project seperti: BASE_DIR / 'subdir'.s
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-local-dev-secret-key'
)

# SECURITY WARNING: don't run with debug turned on in production!
# Ambil dari environment variable (1=True, 0=False), default ke True ('1') jika tidak diset (untuk lokal dev)
DEBUG = os.environ.get('DEBUG', '1') == '1'

# Ambil dari environment variable (dipisah spasi)
ALLOWED_HOSTS_STRING = os.environ.get('ALLOWED_HOSTS')
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(' ') if ALLOWED_HOSTS_STRING else []


# Application
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'users.apps.UsersConfig',
    'tugas_akhir.apps.TugasAkhirConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "digita_admin.urls"

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

WSGI_APPLICATION = "digita_admin.wsgi.application"


# Database
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME', 'digita_db_local'),
        'USER': os.environ.get('DB_USER', 'digitaadmin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'digitaadmin'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
# Catatan: Saat di Docker, nilai di atas akan diambil dari .env via docker-compose.yml

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True

# USE_L10N sudah tidak eksplisit diperlukan di Django 4+, USE_I18N mengaturnya.
# USE_L10N = True

USE_TZ = True

# lokasi file terjemahan
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# Static files
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
# STATIC_ROOT = BASE_DIR / 'staticfiles' # Uncomment jika pakai collectstatic


# Media files (User Uploads) - Placeholder
# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Konfigurasi Tambahan (REST Framework, JWT, CORS, Auth Backends) ---

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # 'DEFAULT_PERMISSION_CLASSES': [ # Opsional: Permission default
    #     'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    # ]
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120), # contoh: 2 jam
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    # "ALGORITHM": "HS256",
    # "SIGNING_KEY": SECRET_KEY, # Menggunakan SECRET_KEY Django secara default
}

# Untuk development, izinkan semua origin. Ganti dengan list spesifik di production.
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:8080", # Contoh port Flutter web dev server
#     "http://127.0.0.1:8080",
#     # Tambahkan origin domain frontend production Anda
# ]
# CORS_ALLOW_CREDENTIALS = True # Jika perlu kirim cookie/auth header

AUTHENTICATION_BACKENDS = [
    'users.backends.NimNikAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Opsional: Untuk otomatis memuat file .env saat menjalankan manage.py secara lokal
# Install dulu: pip install python-dotenv
# Lalu uncomment baris berikut:
# try:
#     from dotenv import load_dotenv
#     load_dotenv()
# except ImportError:
#     pass # Biarkan jika python-dotenv tidak terinstall
