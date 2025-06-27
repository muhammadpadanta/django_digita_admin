import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from decouple import config

# --- Environment Variable Loading ---
# Attempts to load environment variables from a .env file for local development.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Core Django Settings ---
# Defines the base directory of the project.
BASE_DIR = Path(__file__).resolve().parent.parent

# A secret key for a particular Django installation. This is used to provide cryptographic signing.
# It's loaded from an environment variable for security, with a fallback for local development.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-secret-key-fallback')

# A boolean that turns on/off debug mode. Never have debug mode enabled in a production environment.
# '1' is treated as True, otherwise False.
DEBUG = os.environ.get('DEBUG', '1') == '1'

# A list of strings representing the host/domain names that this Django site can serve.
# It's populated from an environment variable, splitting a space-separated string.
ALLOWED_HOSTS_STRING = os.environ.get('ALLOWED_HOSTS')
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(',') if ALLOWED_HOSTS_STRING else ['localhost', '127.0.0.1']


# --- Application Definitions ---
INSTALLED_APPS = [
    # --- Local Apps First ---
    # This ensures your model customizations are loaded before other apps use them.
    'users.apps.UsersConfig',
    'core.apps.CoreConfig',
    'tugas_akhir.apps.TugasAkhirConfig',
    'announcements',


    # --- Third-Party Apps ---
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django.forms',
    'django_rich',
    'storages',  # For AWS S3 storage backend
    'django_cleanup.apps.CleanupConfig',
    'crum',

    # --- Django Core Apps Last ---
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

]

# --- Middleware Configuration ---
# A list of middleware to be executed during the request/response processing.
# Order is important.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # For serving static files in production
    'corsheaders.middleware.CorsMiddleware', # Handles CORS headers
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'core.middleware.AdminSessionTimeoutMiddleware',
]

# --- URL Configuration ---
# The path to the root URLconf module for this project.
ROOT_URLCONF = "digita_admin.urls"

# --- Template Configuration ---
# Settings for Django's template engine.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'], # Directories where Django should look for templates
        "APP_DIRS": True, # Look for templates inside application directories
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

# AWS S3 MEDIA STORAGE CONFIGURATION (FINAL)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ap-southeast-2')

# Standard recommended settings for S3
AWS_S3_FILE_OVERWRITE = False
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com' if AWS_STORAGE_BUCKET_NAME else None

# Use S3 for media storage only if a bucket name is provided.
# Otherwise, Django will fall back to the default local file storage.
if AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# --- WSGI Application ---
# The path to the WSGI application object that Django's built-in servers will use.
WSGI_APPLICATION = "digita_admin.wsgi.application"

# --- Database Configuration ---
# Configures the project's database connection.
# Uses dj_database_url to parse the DATABASE_URL environment variable.
# Provides a fallback to individual environment variables if DATABASE_URL is not set.

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.environ.get('DB_NAME', 'digita_db'),
            'USER': os.environ.get('DB_USER', 'digitaadmin'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }


# --- Password Validation ---
# A list of validators that are used to check the strength of user passwords.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# --- Internationalization & Localization ---
# Settings for language, time zone, and translation support.
LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True # Enable Django's translation system
USE_TZ = True   # Enable timezone-aware datetimes

# Directory where translation files are stored.
LOCALE_PATHS = [
    BASE_DIR / 'locale',
    ]

# --- Static Files Configuration (CSS, JavaScript, Images) ---
# The URL to use when referring to static files located in STATIC_ROOT.
STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
    ]

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Default Primary Key ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework Settings ---
# Configures default settings for Django REST Framework.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# --- Simple JWT (JSON Web Token) Settings ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120), # Lifespan of an access token
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),     # Lifespan of a refresh token
    "ROTATE_REFRESH_TOKENS": False,                  # If True, a new refresh token is issued when one is used
    "BLACKLIST_AFTER_ROTATION": False,               # If True, old refresh tokens are added to a blacklist
}

# --- Deployment Specific Settings (Railway) ---
# Fetches the application URL from Railway's environment variables.
RAILWAY_APP_URL = os.environ.get('RAILWAY_APP_URL')

# A list of trusted origins for unsafe requests (e.g., POST).
# Automatically adds the Railway app URL if it exists.
CSRF_TRUSTED_ORIGINS = []
if RAILWAY_APP_URL:
    CSRF_TRUSTED_ORIGINS.append(RAILWAY_APP_URL)

# --- CORS (Cross-Origin Resource Sharing) Settings ---
# Controls which domains are allowed to make cross-origin requests to your API.
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'True') == 'True'
CORS_ALLOWED_ORIGINS_STRING = os.environ.get('CORS_ALLOWED_ORIGINS')
CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS_STRING.split(' ') if CORS_ALLOWED_ORIGINS_STRING else []

# Fallback to allow all origins if no specific origins are defined and CORS_ALLOW_ALL_ORIGINS is not False.
if not CORS_ALLOWED_ORIGINS and not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOW_ALL_ORIGINS = True

# --- Custom Authentication Backends ---
# Specifies the authentication backends to use for authenticating users.
AUTHENTICATION_BACKENDS = [
    'users.backends.NimNikAuthBackend', # Custom backend
    'django.contrib.auth.backends.ModelBackend', # Default Django backend
]

# --- Email Settings ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('BREVO_EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('BREVO_EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('BREVO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('BREVO_EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('BREVO_DEFAULT_FROM_EMAIL', 'noreply@muhammadpadanta.tech')

# --- Frontend URL Configuration ---
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

LOGIN_URL = 'core:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'

FORM_RENDERER = "django.forms.renderers.DjangoTemplates"


# --- SESSION TIMEOUT CONFIGURATION ---
# The new setting that forces logout when the browser is closed.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Sets the global session expiry to 20 minutes (1200 seconds) for inactivity.
# This will now primarily affect admins due to our middleware.
SESSION_COOKIE_AGE = 1200

# Resets the inactivity timer on each request.
SESSION_SAVE_EVERY_REQUEST = True
# --- END SESSION TIMEOUT CONFIGURATION ---

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'loggers': {
#         'boto3': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'botocore': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#     },
# }

