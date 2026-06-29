#!/usr/bin/env bash
# scripts/deploy.sh
# Zero-downtime production deployment.
# Run on your VPS after pushing code changes.
#
# Usage: bash scripts/deploy.sh [--skip-build]

set -euo pipefail

SKIP_BUILD=false
[[ "${1:-}" == "--skip-build" ]] && SKIP_BUILD=true

log()  { echo "[$(date '+%H:%M:%S')] $1"; }
ok()   { echo "[$(date '+%H:%M:%S')] ✓ $1"; }

log "Starting CineAI production deployment"

# ── Pull latest code ───────────────────────────────────────────────────────────
log "Pulling latest code..."
git pull origin main
ok "Code updated"

# ── Build images ───────────────────────────────────────────────────────────────
if [ "$SKIP_BUILD" = false ]; then
    log "Building Docker images..."
    docker compose -f docker-compose.prod.yml build --parallel
    ok "Images built"
fi

# ── Run database migrations ────────────────────────────────────────────────────
log "Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm backend \
    alembic upgrade head
ok "Migrations applied"

# ── Rolling restart ────────────────────────────────────────────────────────────
log "Restarting backend (rolling)..."
docker compose -f docker-compose.prod.yml up -d --no-deps backend
ok "Backend restarted"

log "Restarting frontend..."
docker compose -f docker-compose.prod.yml up -d --no-deps frontend
ok "Frontend restarted"

log "Reloading Nginx..."
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
ok "Nginx reloaded"

# ── Health check ───────────────────────────────────────────────────────────────
log "Running health check..."
sleep 5
STATUS=$(curl -sf http://localhost/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])" 2>/dev/null || echo "error")
if [ "$STATUS" = "ok" ]; then
    ok "Health check passed"
else
    echo "Health check failed! Status: $STATUS"
    echo "Check logs: docker compose -f docker-compose.prod.yml logs backend --tail=50"
    exit 1
fi

log "Deployment complete 🚀"
