#!/usr/bin/env bash
# Sahaay Multilingual Conversational Voicebot Launcher
# Runs high-performance C++20 backend and React Vite frontend.

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "========================================================"
echo "Sahaay Multilingual Conversational Voicebot (C++ Core)"
echo "Supported Languages: English, Hindi, Gujarati, Marathi"
echo "========================================================"

# 1. Build C++ Backend
echo "Building / verifying C++ backend..."
mkdir -p backend_cpp/build
(
  cd backend_cpp/build
  cmake .. -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1 || cmake .. -DCMAKE_BUILD_TYPE=Release
  make -j$(nproc)
)
echo "C++ backend built successfully."

# 2. Check Node modules for frontend
if [ ! -d "frontend/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi

cleanup() {
  echo ""
  echo "Shutting down Voicebot services..."
  if [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 3. Start C++ Backend
echo "Starting C++ Backend on http://0.0.0.0:8000..."
backend_cpp/build/voicebot_server &
BACKEND_PID=$!

# Wait for backend health
echo "Waiting for C++ backend to initialize..."
for i in {1..20}; do
  if curl -s http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    echo "C++ Backend is ready and healthy."
    break
  fi
  sleep 0.2
done

# 4. Start Frontend
echo "Starting Vite Frontend on http://0.0.0.0:5173..."
(cd frontend && npm run dev -- --host 0.0.0.0 --port 5173) &
FRONTEND_PID=$!

sleep 1

# Detect local IP
LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || hostname -i 2>/dev/null || echo "127.0.0.1")

echo ""
echo "========================================================"
echo "Services are live:"
echo "  Voice Assistant App: http://localhost:5173/"
echo "  Network App:         http://${LOCAL_IP}:5173/"
echo "  C++ Backend Health:  http://localhost:8000/api/health"
echo "========================================================"
echo "Press Ctrl+C to stop all services."

wait
