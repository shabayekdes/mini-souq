# Python version is a build-time argument (Debian bookworm base; bullseye is EOL).
ARG PYTHON_VERSION=3.12-slim-bookworm
FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

# All dependencies ship manylinux wheels (psycopg[binary] bundles libpq,
# Pillow bundles libjpeg), so no compiler or -dev packages are needed.
RUN python -m venv /opt/venv

WORKDIR /code

# Install requirements first so this layer is cached across code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# collectstatic doesn't touch the database or use the secret key, but settings
# require both outside DEBUG mode. These placeholders exist only for this RUN
# step and are not stored in the image config. Real secrets are injected at
# runtime by the platform (e.g. Railway variables) - never as build args.
RUN DJANGO_SECRET_KEY=collectstatic-build-placeholder \
    DATABASE_URL=sqlite://:memory: \
    python manage.py collectstatic --noinput

# Run as an unprivileged user. Only the media directory needs to be writable.
RUN useradd --system --uid 10001 --user-group --no-create-home app \
    && mkdir -p /code/media \
    && chown app:app /code/media \
    && chmod +x scripts/start.sh
USER app

EXPOSE 8000

CMD ["./scripts/start.sh"]
