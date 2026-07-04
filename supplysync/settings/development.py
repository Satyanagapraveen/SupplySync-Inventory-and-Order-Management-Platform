"""
supplysync/settings/development.py
"""
from .base import *
import os
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
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'options': '-c search_path=supplysync,public' 
        }
    }
}

# Redis Cache configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
    }
}

# Celery configuration connecting to our local Docker Redis
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')