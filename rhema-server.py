#!/usr/bin/env python3
"""Rhema local web server: static app + same-origin AI hop.

Why this exists: the browser build cannot call the AI provider directly.
opencode.ai sends no CORS headers, so a plain static host (python -m http.server,
GitHub Pages) makes every AI feature die with "Failed to fetch" while the rest of
the app looks perfectly healthy. The app therefore probes POST /proxy/ai/transport-probe
on launch:

    present  -> keep the fast provider (and its shipped key) and route through us
    absent   -> go direct, and on a browser-blind host fall back to BYOK

This server answers that probe and forwards /proxy/ai/<urlencoded-upstream> to the
provider, streaming SSE straight back so answers type out as they are generated.

    python rhema-server.py            # http://127.0.0.1:8092/
    PORT=8093 python rhema-server.py

Only https upstreams on the allowlist are proxied (no SSRF), and the browser's own
Authorization header is forwarded untouched — the server holds no key of its own.
"""

import json
import os
import sys
import http.client
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8092"))
HOST = os.environ.get("HOST", "127.0.0.1")

# Providers the app can be pointed at. Anything else is refused.
ALLOW_HOSTS = {
    "opencode.ai", "api.deepseek.com", "openrouter.ai", "api.openrouter.ai",
    "api.anthropic.com", "api.openai.com", "api.groq.com",
    "integrate.api.nvidia.com",
}
FORWARD_HEADERS = (
    "authorization", "content-type", "accept", "x-session-id", "x-api-key",
    "x-opencode-session", "anthropic-version",
    "anthropic-dangerous-direct-browser-access", "http-referer", "x-title",
    "user-agent",
)
HOP_BY_HOP = {"host", "content-length", "connection", "keep-alive", "transfer-encoding",
              "upgrade", "proxy-authorization", "te", "trailer"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "RhemaServer/1.0"

    def log_message(self, format, *args):  # noqa: A002 - base class signature; log errors only
        if str(args[1] if len(args) > 1 else "").startswith(("4", "5")):
            sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    # ---------- static ----------
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", ""):
            path = "/index.html"
        rel = os.path.normpath(urllib.parse.unquote(path)).lstrip("\\/")
        full = os.path.join(ROOT, rel)
        if not os.path.abspath(full).startswith(ROOT) or not os.path.isfile(full):
            self._send(404, b"Not found", "text/plain")
            return
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        with open(full, "rb") as fh:
            body = fh.read()
        self._send(200, body, ctype, cache=("no-cache" if rel == "index.html" else "max-age=3600"))

    # ---------- ai hop ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if not self.path.startswith("/proxy/ai/"):
            self._send(404, b"Not found", "text/plain")
            return
        target = self.path[len("/proxy/ai/"):]

        if target == "transport-probe":
            self._send(200, json.dumps({"proxy": "rhema", "ok": True}).encode(), "application/json")
            return

        upstream = urllib.parse.unquote(target)
        parsed = urllib.parse.urlparse(upstream)
        if parsed.scheme != "https" or parsed.hostname not in ALLOW_HOSTS:
            self._send(400, json.dumps({"error": "upstream not allowed", "got": upstream[:200]}).encode(),
                       "application/json")
            return

        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length) if length else b""

        # Forward every client header the upstream may need (the app sends
        # Authorization, content-type, x-opencode-session, anthropic-* ...) minus
        # the hop-by-hop ones that belong to this connection only.
        headers = {}
        for name, val in self.headers.items():
            low = name.lower()
            if low in HOP_BY_HOP:
                continue
            headers[low] = val
        headers["host"] = parsed.hostname

        conn = http.client.HTTPSConnection(parsed.hostname, timeout=180)
        path = parsed.path + (("?" + parsed.query) if parsed.query else "")
        try:
            conn.request("POST", path, body=body, headers=headers)
            resp = conn.getresponse()
        except Exception as exc:  # network failure -> honest 502, the app shows it
            self._send(502, json.dumps({"error": "upstream unreachable", "detail": str(exc)}).encode(),
                       "application/json")
            return

        ctype = resp.getheader("content-type", "application/json")
        streaming = "event-stream" in ctype
        self.send_response(resp.status)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        if streaming:
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            try:
                while True:
                    chunk = resp.read1(4096) if hasattr(resp, "read1") else resp.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                    self.wfile.flush()
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                conn.close()
            return

        payload = resp.read()
        conn.close()
        self._send(resp.status, payload, ctype)

    # ---------- helper ----------
    def _send(self, status, body, ctype, cache="no-store"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    size = os.path.getsize(os.path.join(ROOT, "index.html")) if os.path.exists(os.path.join(ROOT, "index.html")) else 0
    print("Rhema serving %s on http://%s:%d/  (index.html %d bytes, AI hop: /proxy/ai/)" % (ROOT, HOST, PORT, size))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
