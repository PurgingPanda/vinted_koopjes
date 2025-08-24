# PostgreSQL settings for Vinted Koopjes
from .settings import *
import os

# Database configuration for PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'vinted_koopjes'),
        'USER': os.getenv('DB_USER', 'vinted'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),  # Set password if needed
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Performance optimizations for PostgreSQL
DATABASES['default']['OPTIONS'].update({
    'MAX_CONNS': 20,
    'OPTIONS': {
        'MAX_CONNS': 20,
        'autocommit': True,
    }
})

# Connection pooling (optional)
# DATABASES['default']['CONN_MAX_AGE'] = 60

print("📊 Using PostgreSQL database configuration")
print(f"Database: {DATABASES['default']['NAME']}@{DATABASES['default']['HOST']}:{DATABASES['default']['PORT']}")