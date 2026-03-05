# =========================
# BASE STAGE
# =========================
FROM python:3.13-slim AS base

RUN apt-get update && \
    apt-get install -y build-essential curl && \
    apt-get clean

WORKDIR /app

# Install pip-tools so pip can understand pyproject.toml deps
RUN pip install pip-tools

# Copy dependency files
COPY pyproject.toml .

# Compile requirements.txt from pyproject.toml
RUN pip-compile pyproject.toml --output-file=requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files (but NOT the db folder contents)
COPY . .

# =========================
# TAILWIND BUILD STAGE
# =========================
FROM base AS tailwind

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

RUN python manage.py tailwind install
RUN python manage.py tailwind build
RUN python manage.py collectstatic --noinput

# =========================
# FINAL RUNTIME IMAGE
# =========================
FROM python:3.13-slim AS final

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=app.settings

# Copy pyproject and compiled requirements
COPY pyproject.toml .
COPY --from=base /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# Copy tailwind output
COPY --from=tailwind /app/staticfiles /app/staticfiles

# Create db directory with proper permissions
RUN mkdir -p /app/db && chmod 777 /app/db

# Entrypoint with Gunicorn - increased timeout and async workers
RUN printf '#!/bin/sh\n\
python manage.py migrate --noinput\n\
exec gunicorn app.wsgi:application \\\n\
  --bind 0.0.0.0:8965 \\\n\
  --workers 3 \\\n\
  --worker-class gevent \\\n\
  --worker-connections 1000 \\\n\
  --timeout 300 \\\n\
  --access-logfile - \\\n\
  --error-logfile - \\\n\
  --log-level info\n' \
> /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000
CMD ["/entrypoint.sh"]