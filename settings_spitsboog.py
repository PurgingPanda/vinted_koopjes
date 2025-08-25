# PostgreSQL settings for spitsboog.org server
from vinted_koopjes.settings import *
import os

# Force network scraper mode for this configuration
os.environ['VINTED_SCRAPER_MODE'] = 'network'
print("🌐 FORCED NETWORK SCRAPER MODE: Settings file set VINTED_SCRAPER_MODE=network")

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
DEBUG_DB = False

print("🚀 Using PostgreSQL database on spitsboog.org")
print(f"Database: {DATABASES['default']['NAME']}@{DATABASES['default']['HOST']}:{DATABASES['default']['PORT']}")
print(f"User: {DATABASES['default']['USER']}")

# Configure logging for application (always enabled)
import logging

class BlockingStateFilter(logging.Filter):
    """Filter out BlockingState database queries to reduce log spam"""
    def filter(self, record):
        # Filter out BlockingState SELECT queries
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            if 'watches_blockingstate' in message.lower() and 'select' in message.lower():
                return False
        return True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'no_blocking_state': {
            '()': BlockingStateFilter,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'filters': ['no_blocking_state'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'watches': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'vinted_scraper': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Database logging disabled (DEBUG_DB = False)