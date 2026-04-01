#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v pdm >/dev/null 2>&1; then
  echo "Install PDM: https://pdm-project.org/latest/"
  exit 1
fi

pdm install -G dev -G test -G lint
echo "Bootstrap complete. Copy .env.example to .env and run: make docker-up && make migrate"
