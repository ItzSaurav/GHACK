#!/usr/bin/env bash
# Sahaay & Seva Vaani Unified Launcher
# Hosts both the FastAPI backend and Vite frontend services.

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "========================================================"
echo "Sahaay Government Schemes Portal & Seva Vaani Assistant"
echo "========================================================"

# Check Python environment
if [ ! -d ".venv" ]; then
  echo "Virtual environment .venv not found. Creating..."
  python3 -m venv .venv
  .venv/bin/pip install -r backend/requirements.txt
fi

# Check Node modules
if [ ! -d "frontend/node_modules" ]; then
  echo "Node modules not found in frontend/. Installing..."
  (cd frontend && npm install)
fi

cleanup() {
  echo ""
  echo "Shutting down Sahaay services..."
  if [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start Backend
echo "Starting FastAPI Backend on http://0.0.0.0:8000..."
.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend health
echo "Waiting for backend to initialize..."
for i in {1..15}; do
  if curl -s http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    echo "Backend is ready and healthy."
    break
  fi
  sleep 0.5
done

# Start Frontend
echo "Starting Vite Frontend on http://0.0.0.0:5173..."
(cd frontend && npm run dev -- --host 0.0.0.0 --port 5173) &
FRONTEND_PID=$!

sleep 1

# Detect local IP
LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || hostname -i 2>/dev/null || echo "127.0.0.1")

echo ""
echo "========================================================"
echo "Services are live:"
echo "  Local Portal:        http://localhost:5173/"
echo "  Network Portal:      http://${LOCAL_IP}:5173/"
echo "  Backend API Docs:    http://localhost:8000/docs"
echo "  Health Endpoint:     http://localhost:8000/api/v1/health"
echo "========================================================"
echo "Press Ctrl+C to stop all services."

wait
