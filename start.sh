#!/bin/bash
# start.sh — launch DevToolBox backend + frontend on macOS
# Usage: ./start.sh
#        ./start.sh stop   ← kill both servers

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv/bin/python"
BACKEND_LOG="$ROOT/backend.log"
FRONTEND_LOG="$ROOT/frontend.log"
BACKEND_PORT=5001
FRONTEND_PORT=8080

# ── Stop mode ────────────────────────────────────────────────────────────────
if [[ "$1" == "stop" ]]; then
  echo "Stopping DevToolBox servers…"
  lsof -ti :$BACKEND_PORT  | xargs kill -9 2>/dev/null && echo "  Backend stopped"  || echo "  Backend was not running"
  lsof -ti :$FRONTEND_PORT | xargs kill -9 2>/dev/null && echo "  Frontend stopped" || echo "  Frontend was not running"
  exit 0
fi

# ── Kill any stale servers on those ports ────────────────────────────────────
lsof -ti :$BACKEND_PORT  | xargs kill -9 2>/dev/null
lsof -ti :$FRONTEND_PORT | xargs kill -9 2>/dev/null
sleep 0.5

# ── Backend ───────────────────────────────────────────────────────────────────
echo "Starting backend  → http://localhost:$BACKEND_PORT"
(cd "$ROOT/backend" && PORT=$BACKEND_PORT "$VENV" -u app.py > "$BACKEND_LOG" 2>&1) &
BACKEND_PID=$!

# Wait until Flask is accepting connections (up to 10 s)
for i in $(seq 1 20); do
  sleep 0.5
  if lsof -ti :$BACKEND_PORT > /dev/null 2>&1; then
    echo "  Backend ready (pid $BACKEND_PID)"
    break
  fi
  if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "  ERROR: Backend crashed. Check $BACKEND_LOG"
    cat "$BACKEND_LOG"
    exit 1
  fi
done

# ── Frontend ──────────────────────────────────────────────────────────────────
echo "Starting frontend → http://localhost:$FRONTEND_PORT"
(cd "$ROOT/frontend" && npm run dev > "$FRONTEND_LOG" 2>&1) &
FRONTEND_PID=$!

# Wait until Vite is ready
for i in $(seq 1 20); do
  sleep 0.5
  if grep -q "Local:" "$FRONTEND_LOG" 2>/dev/null; then
    echo "  Frontend ready (pid $FRONTEND_PID)"
    break
  fi
  if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "  ERROR: Frontend crashed. Check $FRONTEND_LOG"
    cat "$FRONTEND_LOG"
    exit 1
  fi
done

# ── Open browser ──────────────────────────────────────────────────────────────
sleep 0.5
open "http://localhost:$FRONTEND_PORT" 2>/dev/null

echo ""
echo "DevToolBox is running."
echo "  Frontend → http://localhost:$FRONTEND_PORT"
echo "  Backend  → http://localhost:$BACKEND_PORT"
echo "  Logs     → $BACKEND_LOG  |  $FRONTEND_LOG"
echo ""
echo "Press Ctrl+C to stop both servers."

# ── Keep script alive; Ctrl-C kills both ─────────────────────────────────────
trap "echo ''; echo 'Stopping…'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
