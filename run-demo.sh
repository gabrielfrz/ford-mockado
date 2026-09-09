#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
# Prefer the user's installed tools; Codex's bundled runtime also works on this Mac.
RUNTIME="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies"
if ! command -v node >/dev/null && [ -x "$RUNTIME/node/bin/node" ]; then
  export PATH="$RUNTIME/node/bin:$PATH"
fi
if ! command -v pnpm >/dev/null && [ -x "$RUNTIME/bin/fallback/pnpm" ]; then
  export PATH="$RUNTIME/bin/fallback:$PATH"
fi
command -v node >/dev/null || { echo 'Install Node.js 22.12+ first.'; exit 1; }
command -v pnpm >/dev/null || { echo 'Install pnpm: npm install -g pnpm@11'; exit 1; }
python3 - <<'PY'
import socket
for port in [4200, 8000]:
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
        except OSError:
            raise SystemExit(f'Porta {port} ocupada. Encerre a execução anterior com Control+C e tente novamente.')
PY
if [ ! -x back/.venv/bin/python ]; then python3 -m venv back/.venv; fi
if ! back/.venv/bin/python -c 'import fastapi, uvicorn, openpyxl' 2>/dev/null; then
  back/.venv/bin/python -m pip install -r back/requirements-demo.txt
fi
(
  cd front/dandr-web
  if [ ! -d node_modules ]; then pnpm install --frozen-lockfile; fi
  NG_BUILD_MAX_WORKERS=2 node node_modules/@angular/cli/bin/ng.js build --progress=false
)
backend_pid=''
frontend_pid=''
cleanup() {
  [ -z "$backend_pid" ] || kill "$backend_pid" 2>/dev/null || true
  [ -z "$frontend_pid" ] || kill "$frontend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
back/.venv/bin/python -m uvicorn app.main:app --app-dir back --host 127.0.0.1 --port 8000 &
backend_pid=$!
back/.venv/bin/python scripts/serve_front.py &
frontend_pid=$!
echo 'Dashboard: http://localhost:4200 | API: http://localhost:8000/docs | Ctrl+C to stop'
# Detect if either server fails and clean up the other one.
while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do sleep 1; done
exit 1
