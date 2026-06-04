"""
supplysync/settings/development.py
"""
from .base import *

# Enable debug mode for local development
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database configuration connecting to our local Docker Postgres
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'supplysync_db',
        'USER': 'supplysync_user',
        'PASSWORD': 'supplysync_pass',
        'HOST': 'localhost', # run django locally, outside docker
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c search_path=supplysync,public' 
        }
    }
}

# Redis Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://localhost:6379/1",
    }
}

# Celery configuration connecting to our local Docker Redis
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'