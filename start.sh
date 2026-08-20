#!/usr/bin/env bash
# BioArbitrage MVP — one-command local startup (bash/macOS/Linux)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

echo -e "\n\033[36m[BioArbitrage] Starting backend...\033[0m"

# Backend
(
  cd "$BACKEND"
  if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
  else
    source venv/bin/activate
  fi
  echo -e "\033[32mStarting FastAPI on http://localhost:8000\033[0m"
  uvicorn main:app --reload --port 8000
) &
BACKEND_PID=$!

sleep 2

echo -e "\033[36m[BioArbitrage] Starting frontend...\033[0m"

# Frontend
(
  cd "$FRONTEND"
  if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
  fi
  echo -e "\033[32mStarting Vite dev server on http://localhost:5173\033[0m"
  npm run dev
) &
FRONTEND_PID=$!

echo -e "\n\033[32m[BioArbitrage] Both services running.\033[0m"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."

# Wait and cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
