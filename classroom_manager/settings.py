import os
from pathlib import Path
import os

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', default='django-insecure-change-this-key-in-production')
DEBUG = os.environ.get('DEBUG', default=True) == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RoleRequiredMiddleware',
]

ROOT_URLCONF = 'classroom_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_context',
            ],
        },
    },
]

from mongoengine import connect # type: ignore

WSGI_APPLICATION = 'classroom_manager.wsgi.application'

# MongoDB Configuration
MONGODB_HOST = os.environ.get('MONGODB_HOST', default='localhost')
MONGODB_PORT = int(os.environ.get('MONGODB_PORT', default='27017'))
MONGODB_NAME = os.environ.get('MONGODB_NAME', default='classroom_db')
MONGODB_USER = os.environ.get('MONGODB_USER', default='')
MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD', default='')

# Connect to MongoDB
connect(
    db=MONGODB_NAME,
    host=MONGODB_HOST,
    port=MONGODB_PORT,
    username=MONGODB_USER,
    password=MONGODB_PASSWORD,
    alias='default'
)

# Django doesn't use traditional DATABASES for MongoDB, but we keep this for sessions
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = int(os.environ.get('SESSION_COOKIE_AGE', default='7200'))
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', default='False') == 'True'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Settings
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', default='False') == 'True'
CSRF_COOKIE_HTTPONLY = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = os.environ.get('MEDIA_URL', default='/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, os.environ.get('MEDIA_ROOT', default='media'))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Caching (for rate limiting)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
