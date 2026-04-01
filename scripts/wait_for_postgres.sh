#!/usr/bin/env bash
set -euo pipefail
host="${1:-localhost}"
port="${2:-5432}"
user="${3:-scoring}"
db="${4:-scoring}"
for i in $(seq 1 60); do
  if pg_isready -h "$host" -p "$port" -U "$user" -d "$db" >/dev/null 2>&1; then
    echo "Postgres is ready."
    exit 0
  fi
  echo "Waiting for Postgres... ($i)"
  sleep 1
done
echo "Postgres did not become ready in time."
exit 1
