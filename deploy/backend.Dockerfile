FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY deploy/requirements-web.txt /app/deploy/requirements-web.txt
RUN pip install --no-cache-dir -r deploy/requirements-web.txt \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home app \
    && mkdir -p /data /media /static \
    && chown app:app /data /media /static
COPY --chown=app:app backend_django /app/backend_django
COPY --chown=app:app demo_assets /app/demo_assets
COPY --chown=app:app deploy /app/deploy
USER app
WORKDIR /app/backend_django
ENTRYPOINT ["/bin/sh", "/app/deploy/entrypoint.sh"]
CMD ["gunicorn", "--config", "/app/deploy/gunicorn.conf.py", "backend_django.wsgi:application"]
