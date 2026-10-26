#!/usr/bin/env bash
# Start the Rhema web app locally, then open it in the browser.
#   bash ~/blueprints/rhema-web/start.sh          # 127.0.0.1:8092
#   PORT=8093 bash start.sh                       # another port
#   HOST=0.0.0.0 bash start.sh                    # also reachable from a phone on the LAN
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8092}"

if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:${PORT}/"; then
  echo "already running on http://127.0.0.1:${PORT}/"
else
  cd "$DIR"
  nohup python rhema-server.py >/tmp/rhema-server.log 2>&1 &
  sleep 2
  curl -s -o /dev/null -w "started: %{http_code}\n" "http://127.0.0.1:${PORT}/"
fi
curl -s -X POST "http://127.0.0.1:${PORT}/proxy/ai/transport-probe" >/dev/null \
  && echo "AI hop: /proxy/ai/ responding (AI works in the browser)"
cd /c && C:/WINDOWS/explorer.exe "http://127.0.0.1:${PORT}/" >/dev/null 2>&1 || true
