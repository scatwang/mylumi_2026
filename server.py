#!/usr/bin/env python3
"""
Simple local preview server for NorCal FLL BIOGLOW 2026 Web Analytics
"""
import http.server
import os
from pathlib import Path
import socketserver
import sys

PORT = 8088
WEB_DIR = Path(__file__).parent / "web"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        # Disable caching for rapid local preview and avoid stale js files
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    # Use ThreadingHTTPServer to handle multiple concurrent requests without socket deadlock
    server_address = ("", port)
    with http.server.ThreadingHTTPServer(server_address, Handler) as httpd:
        print(f"🚀 NorCal FLL BIOGLOW Analytics Web Server running at:")
        print(f"👉 http://localhost:{port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    main()
