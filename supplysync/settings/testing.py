from .base  import * # Import all default settings

# 1. Use an in-memory database for extreme speed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# 2. Disable password hashing to speed up tests (hashing is CPU-intensive)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# 3. Use a dummy email backend so we don't accidentally send real emails
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
# Synchronous Celery task execution
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# SQLite doesn't support schemas or some options, so make sure they are not applied.
# In memory cache for testing to avoid Redis requirement.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "testing-cache",
    }
}