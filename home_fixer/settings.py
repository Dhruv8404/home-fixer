from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url
from datetime import timedelta

load_dotenv()

# ================== ENV ==================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "home-fixer-production.up.railway.app",
    "localhost",
    "127.0.0.1",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ================== PAYMENT ==================
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_CURRENCY = "INR"
RAZORPAY_PAYMENT_CAPTURE = 1

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# ================== EMAIL ==================
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "").replace(" ", "")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 10
OTP_PRINT_IN_TERMINAL = os.getenv("OTP_PRINT_IN_TERMINAL", "False") == "True"

# ================== APPS ==================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_yasg',
    'cloudinary',
    'cloudinary_storage',
    "channels",

    'home',
]

AUTH_USER_MODEL = 'home.User'

# ================== MIDDLEWARE ==================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    # ✅ Keep CSRF (safe for admin/web)
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ================== CORS ==================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-flutter-app-domain.com"
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_CREDENTIALS = True

# ================== URL ==================
ROOT_URLCONF = 'home_fixer.urls'

# ================== TEMPLATES ==================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'home_fixer.wsgi.application'
ASGI_APPLICATION = "homefixerapi.asgi.application"

# ================== DATABASE ==================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "homefixer"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "newpassword"),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "OPTIONS": {
                "sslmode": "require",
            },
            "CONN_MAX_AGE": 0,
        }
    }

# ================== PASSWORD ==================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ================== INTERNATIONAL ==================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ================== STATIC ==================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ================== CLOUDINARY ==================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv("CLOUDINARY_CLOUD_NAME"),
    'API_KEY': os.getenv("CLOUDINARY_API_KEY"),
    'API_SECRET': os.getenv("CLOUDINARY_API_SECRET"),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ================== DRF ==================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # ✅ No CSRF issue
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# ================== JWT (🔥 LONG SESSION FIX) ==================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),      # ✅ long login
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),    # ✅ long session

    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ================== SWAGGER ==================
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'PERSIST_AUTH': True,
    'REFETCH_SCHEMA_WITH_AUTH': True,
    'DEFAULT_API_URL': 'https://home-fixer-production.up.railway.app',

    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter: Bearer <your access token>',
        }
    },
}

# ================== CHANNELS ==================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}