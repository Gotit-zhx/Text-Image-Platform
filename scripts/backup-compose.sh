#!/bin/sh
# Consistent SQLite + media snapshot. Never removes application data.
set -eu
cd "$(dirname "$0")/.."
umask 077
env_file=${COMPOSE_ENV_FILE:-.env.compose}
output=${1:-backups/baicaoyuan-$(date -u +%Y%m%dT%H%M%SZ).tar.gz}
partial="$output.partial"
if [ -e "$output" ] || [ -e "$partial" ]; then
  printf '%s\n' 'Backup destination already exists; choose a new filename.' >&2
  exit 1
fi
mkdir -p "$(dirname "$output")"
compose() { docker compose --env-file "$env_file" "$@"; }
restart_app=false
finish() {
  result=$?
  trap - 0
  if [ "$restart_app" = true ]; then
    compose start app >&2 || result=1
  fi
  if [ "$result" -ne 0 ]; then rm -f "$partial"; fi
  exit "$result"
}
trap finish 0
trap 'exit 130' INT
trap 'exit 143' TERM
if [ -n "$(compose ps --status running -q app)" ]; then
  restart_app=true
  compose stop app >&2
fi
compose run --rm --no-deps -T app python -c '
import os, sqlite3, sys, tarfile
from pathlib import Path
source = Path("/data/db.sqlite3")
if not source.is_file():
    raise SystemExit("No database found; start and initialize the stack first.")
snapshot = Path("/data/.backup-snapshot.sqlite3")
try:
    with sqlite3.connect(source) as db, sqlite3.connect(snapshot) as copy:
        db.backup(copy)
        if copy.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit("Database integrity check failed.")
    with tarfile.open(fileobj=sys.stdout.buffer, mode="w|gz") as archive:
        archive.add(snapshot, arcname="db.sqlite3")
        archive.add("/media", arcname="media")
finally:
    snapshot.unlink(missing_ok=True)
' > "$partial"
mv "$partial" "$output"
printf 'Backup saved: %s\n' "$output"
