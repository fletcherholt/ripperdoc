#!/usr/bin/env python3
"""Browser-mode launcher for the Night City Save Editor.

Stdlib only (no webview backend), so it runs anywhere with a browser — ideal
for the Steam Deck where pywebview's GTK/Qt backend is a pain on the immutable
OS. Serves the web/ UI and exposes the same Api over a tiny JSON POST endpoint
at /api/<method>. The front end auto-detects this mode when window.pywebview is
absent and talks to it with fetch().

Usage:  python3 server.py [--port 8770] [--no-browser]
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from app import Api  # noqa: E402

WEB = os.path.join(HERE, "web")
api = Api()

# browse_folder relies on a webview window; give a stdlib fallback that just
# returns None so the front end falls back to manual path entry.
api.browse_folder = lambda: None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=WEB, **k)

    def log_message(self, *a):
        pass

    def do_POST(self):
        if not self.path.startswith("/api/"):
            self.send_error(404)
            return
        method = self.path[len("/api/"):]
        fn = getattr(api, method, None)
        if not callable(fn) or method.startswith("_"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"[]"
        try:
            args = json.loads(raw or b"[]")
            if not isinstance(args, list):
                args = [args]
            result = fn(*args)
        except Exception as e:  # noqa
            result = {"ok": False, "error": str(e)}
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    port = 8770
    open_browser = "--no-browser" not in sys.argv
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/index.html"
    print(f"NIGHT CITY SAVE EDITOR — jack in at {url}")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\ndelta out, choom")


if __name__ == "__main__":
    main()
