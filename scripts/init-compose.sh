#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
umask 077
mkdir -p .secrets
chmod 700 .secrets
if [ ! -s .secrets/django_secret_key ]; then
  openssl rand -hex 48 > .secrets/django_secret_key
fi
if [ ! -f .secrets/smtp_password ]; then
  : > .secrets/smtp_password
fi
# Compose file-backed secrets are bind mounts on Linux. The containing host
# directory is private; readable files let the unprivileged app use the mounts.
chmod 444 .secrets/django_secret_key .secrets/smtp_password
if [ ! -f .env.compose ]; then
  cp .env.compose.example .env.compose
fi
chmod 600 .env.compose
printf '%s\n' 'Local Compose settings ready. Edit .env.compose, then run:' \
  'docker compose --env-file .env.compose up -d --build'
