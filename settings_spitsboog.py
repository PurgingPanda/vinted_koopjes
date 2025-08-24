# PostgreSQL settings for spitsboog.org server
from vinted_koopjes.settings import *
import os

# Database configuration for PostgreSQL on spitsboog.org
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vinted_koopjes',
        'USER': 'vinted',
        'PASSWORD': 'vintedbroljwz',
        'HOST': 'spitsboog.org',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'prefer',  # Use SSL if available
        },
        'CONN_MAX_AGE': 60,  # Connection pooling
    }
}

# Performance optimizations for remote PostgreSQL
# MAX_CONNS is not a valid PostgreSQL connection option

# Debug database connection
DEBUG_DB = True

print("🚀 Using PostgreSQL database on spitsboog.org")
print(f"Database: {DATABASES['default']['NAME']}@{DATABASES['default']['HOST']}:{DATABASES['default']['PORT']}")
print(f"User: {DATABASES['default']['USER']}")

# Optional: Add database connection logging
if DEBUG_DB:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }