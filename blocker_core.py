import os
import json

REDIRECT_IP = "127.0.0.1"
WHITELIST_FILE = "whitelist.json"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if os.name == "nt" else "/etc/hosts"

def load_whitelist():
    try:
        with open(WHITELIST_FILE, "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_whitelist(sites):
    with open(WHITELIST_FILE, "w") as f:
        json.dump(list(sites), f, indent=4)

def generate_blocklist(whitelist):
    base_blocklist = [
        "google.com", "youtube.com", "reddit.com", "twitter.com",
        "facebook.com", "instagram.com", "netflix.com", "pinterest.com"
    ]
    return [site for site in base_blocklist if site not in whitelist]

def block_all_except_whitelist():
    whitelist = load_whitelist()
    blocked_sites = []

    with open(HOSTS_PATH, "r") as file:
        lines = file.readlines()

    # Remove previously added redirects
    lines = [line for line in lines if REDIRECT_IP not in line]

    for site in generate_blocklist(whitelist):
        blocked_sites.append(f"{REDIRECT_IP} {site}\n")
        blocked_sites.append(f"{REDIRECT_IP} www.{site}\n")

    with open(HOSTS_PATH, "w") as file:
        file.writelines(lines)
        file.writelines(blocked_sites)

def unblock_all():
    with open(HOSTS_PATH, "r") as file:
        lines = file.readlines()

    lines = [line for line in lines if REDIRECT_IP not in line]

    with open(HOSTS_PATH, "w") as file:
        file.writelines(lines)


import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

server_thread = None
httpd = None

class FocusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(bytes("""
            <html>
            <head><title>Stay Focused</title></head>
            <body style="text-align:center; font-family:sans-serif; padding-top:50px;">
                <h1>This site is blocked!</h1>
                <p>You're in Focus Mode. Get back to work!</p>
                <p><em>“Discipline is choosing between what you want now and what you want most.”</em></p>
            </body>
            </html>
        """, "utf-8"))

def run_focus_server():
    global httpd
    try:
        server_address = ('', 80)
        httpd = HTTPServer(server_address, FocusHandler)
        print("⚡ Focus server running on http://127.0.0.1:80")
        httpd.serve_forever()
    except PermissionError:
        print("❌ Admin rights required to run server on port 80.")

def start_focus_server():
    global server_thread
    server_thread = threading.Thread(target=run_focus_server, daemon=True)
    server_thread.start()

def stop_focus_server():
    global httpd
    if httpd:
        httpd.shutdown()
        print("🛑 Focus server stopped.")
