#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if ! command -v docker >/dev/null; then
  echo 'Install Docker Desktop (Mac/Windows) or Docker Engine + Compose (Linux), then run ./setup.sh again.' >&2
  echo 'https://docs.docker.com/get-started/get-docker/' >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo 'Start Docker Desktop or your Docker daemon, then rerun ./setup.sh.' >&2
  exit 1
fi
if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
elif command -v docker-compose >/dev/null; then
  compose=(docker-compose)
else
  echo 'Docker Compose is required. Install it from https://docs.docker.com/compose/install/' >&2
  exit 1
fi
if [[ ! -f .env ]]; then cp .env.example .env; fi
"${compose[@]}" up -d --build
url='http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=remote'
echo "Desktop: $url"
echo 'First launch can take several minutes. See README.md; choose Continue locally if AliasMode asks.'
if command -v open >/dev/null; then open "$url";
elif command -v xdg-open >/dev/null; then xdg-open "$url" >/dev/null 2>&1 || true; fi
