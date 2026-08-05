#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    echo "Neither 'docker compose' nor 'docker-compose' found." >&2
    echo "Install Docker Compose plugin, or place docker-compose in PATH." >&2
    exit 1
  fi
}

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "created .env from .env.example"
fi

echo "starting infrastructure (postgres, redis, mosquitto)..."
compose up -d

echo "waiting for postgres..."
for _ in $(seq 1 30); do
  if compose exec -T postgres pg_isready -U nanexus -d nanexus >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -e .

echo ""
echo "Infra is up. In separate terminals (with venv activated):"
echo "  source .venv/bin/activate"
echo "  uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000"
echo "  python -m services.mqtt_listener.main"
echo "  python -m services.ai_worker.main"
echo ""
echo "Then seed demo events:"
echo "  python scripts/seed_events.py"
echo "  python scripts/build_summary.py"
echo "  curl -s localhost:8000/timeline | python -m json.tool"
