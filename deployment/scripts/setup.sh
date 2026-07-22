#!/usr/bin/env bash
# ====================================================
# Setup Development Environment
# ====================================================
# Installs backend & frontend dependencies,
# creates .env files from examples.
# ====================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "🚀 Setting up development environment..."

# --- Backend ---
echo ""
echo "📦 Setting up backend..."
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ✅ Created backend/.env (please edit with your secrets)"
fi
cd ..

# --- Frontend ---
echo ""
echo "📦 Setting up frontend..."
cd frontend
if ! command -v pnpm &> /dev/null; then
    echo "   ⚠️  pnpm not found, using npm instead"
    npm install
else
    pnpm install
fi
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ✅ Created frontend/.env (please edit with your secrets)"
fi
cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env and frontend/.env with your secrets"
echo "  2. Place ML artifacts in backend/app/ml_artifacts/"
echo "  3. Run database migrations (see database/README.md)"
echo "  4. Start backend:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "  5. Start frontend: cd frontend && pnpm dev"
