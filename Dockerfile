FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /code

# Install Python dependencies
COPY requirements-production.txt /code/
RUN pip install --no-cache-dir -r requirements-production.txt

# Install playwright
RUN playwright install chromium

# Copy project
COPY . /code/

# Collect static files
RUN python manage.py collectstatic --noinput --settings=production_settings

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /code
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "vinted_koopjes.wsgi:application"]