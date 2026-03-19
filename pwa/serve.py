#!/usr/bin/env python3
"""PWA için yerel HTTP sunucusu (port 3000)"""
import http.server, socketserver, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()
    def log_message(self, fmt, *args):
        pass  # sessiz mod

PORT = 3000
print(f"PWA çalışıyor → http://localhost:{PORT}")
print(f"Telefonda kullanmak için → http://<bilgisayar-ip>:{PORT}")
print("Durdurmak için Ctrl+C")
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
