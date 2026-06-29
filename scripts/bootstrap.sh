#!/usr/bin/env bash
# scripts/bootstrap.sh
# Full local development environment setup in one command.
# Run from project root: bash scripts/bootstrap.sh
#
# Prerequisites: Docker, Python 3.11+, Node 20+

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

log()  { echo -e "${CYAN}[CineAI]${RESET} $1"; }
ok()   { echo -e "${GREEN}✓${RESET} $1"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $1"; }
bold() { echo -e "${BOLD}$1${RESET}"; }

echo ""
bold "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bold "  CineAI — Local Development Bootstrap"
bold "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Check prerequisites ─────────────────────────────────────────────────────
log "Checking prerequisites..."
command -v docker   >/dev/null || { echo "Docker not found — install from docker.com"; exit 1; }
command -v python3  >/dev/null || { echo "Python 3 not found"; exit 1; }
command -v node     >/dev/null || { echo "Node.js not found — install from nodejs.org"; exit 1; }
ok "Docker, Python, Node found"

# ── 2. Environment files ───────────────────────────────────────────────────────
log "Setting up environment files..."

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    warn "Created backend/.env — fill in TMDB_API_KEY before continuing"
    warn "Get a free key at: https://www.themoviedb.org/settings/api"
else
    ok "backend/.env already exists"
fi

if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.example frontend/.env.local
    ok "Created frontend/.env.local"
else
    ok "frontend/.env.local already exists"
fi

# ── 3. Start infrastructure ────────────────────────────────────────────────────
log "Starting infrastructure (PostgreSQL, Qdrant, Redis)..."
docker compose up postgres qdrant redis -d
ok "Infrastructure started"

# Wait for PostgreSQL to be healthy
log "Waiting for PostgreSQL to be ready..."
for i in $(seq 1 30); do
    if docker compose exec postgres pg_isready -U postgres -q 2>/dev/null; then
        ok "PostgreSQL ready"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "PostgreSQL didn't start in time"
        exit 1
    fi
done

# ── 4. Backend setup ───────────────────────────────────────────────────────────
log "Setting up Python virtual environment..."
cd backend

if [ ! -d .venv ]; then
    python3 -m venv .venv
    ok "Created .venv"
fi

source .venv/bin/activate

log "Installing Python dependencies (this takes a few minutes on first run)..."
# Install CPU-only PyTorch first to avoid pulling the massive CUDA version
pip install --quiet torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu
pip install --quiet -r requirements.txt
ok "Python dependencies installed"

log "Running database migrations..."
alembic upgrade head
ok "Migrations applied"

log "Pre-downloading sentence-transformers model..."
python3 -c "
from sentence_transformers import SentenceTransformer
print('Downloading all-MiniLM-L6-v2...')
SentenceTransformer('all-MiniLM-L6-v2')
print('Model ready')
"
ok "Embedding model downloaded"

cd ..

# ── 5. Frontend setup ──────────────────────────────────────────────────────────
log "Installing frontend dependencies..."
cd frontend
npm install --silent
ok "Frontend dependencies installed"
cd ..

# ── 6. Done ────────────────────────────────────────────────────────────────────
echo ""
bold "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bold "  Bootstrap complete! Start the app:"
bold "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "  ${CYAN}Terminal 1 — Backend:${RESET}"
echo    "    cd backend && source .venv/bin/activate"
echo    "    uvicorn app.main:app --reload"
echo    "    → http://localhost:8000/docs"
echo ""
echo -e "  ${CYAN}Terminal 2 — Frontend:${RESET}"
echo    "    cd frontend && npm run dev"
echo    "    → http://localhost:3000"
echo ""
warn "Make sure TMDB_API_KEY is set in backend/.env"
echo ""
