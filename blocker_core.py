import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from platformdirs import user_data_dir # Import to get the correct data directory

# --- Configuration ---
REDIRECT_IP = "127.0.0.1"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if os.name == "nt" else "/etc/hosts"

# Database path (consistent with time_controller.py)
APP_NAME = "FocusModeApp" # Make sure this matches your time_controller.py
APP_AUTHOR = "JoshiAarya" # Make sure this matches your time_controller.py
DATA_DIR = user_data_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
os.makedirs(DATA_DIR, exist_ok=True) # Ensure the directory exists
DB_FILE = os.path.join(DATA_DIR, "focus_data.db") # Same DB file as time_controller

# --- Database Functions ---

def init_db():
    """Initializes the SQLite database and creates the blocklist table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_url TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_to_blocklist(site_url):
    """Adds a site to the blocklist in the database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO blocklist (site_url) VALUES (?)", (site_url,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Site already exists
        return False
    finally:
        conn.close()

def remove_from_blocklist(site_url):
    """Removes a site from the blocklist in the database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blocklist WHERE site_url = ?", (site_url,))
    conn.commit()
    conn.close()

def get_blocklist():
    """Retrieves all blocked sites from the database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT site_url FROM blocklist")
    sites = {row[0] for row in cursor.fetchall()} # Return as a set for efficient lookup
    conn.close()
    return sites

# --- Hosts File Manipulation ---

def block_sites():
    """Blocks sites by modifying the hosts file based on the database blocklist."""
    blocked_sites = get_blocklist()
    
    with open(HOSTS_PATH, "r") as file:
        lines = file.readlines()

    # Remove previously added redirects to avoid duplicates
    lines = [line for line in lines if REDIRECT_IP not in line]

    new_block_entries = []
    for site in blocked_sites:
        new_block_entries.append(f"{REDIRECT_IP} {site}\n")
        # Optionally block www. subdomain as well
        if not site.startswith("www."):
            new_block_entries.append(f"{REDIRECT_IP} www.{site}\n")

    with open(HOSTS_PATH, "w") as file:
        file.writelines(lines) # Write original lines back
        file.writelines(new_block_entries) # Append new block entries

def unblock_all():
    """Removes all custom redirects from the hosts file."""
    with open(HOSTS_PATH, "r") as file:
        lines = file.readlines()

    # Keep only lines that do NOT contain our redirect IP
    lines = [line for line in lines if REDIRECT_IP not in line]

    with open(HOSTS_PATH, "w") as file:
        file.writelines(lines)

# --- Local HTTP Server for Blocked Sites ---

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
        # Use 'localhost' explicitly, or '' to bind to all available interfaces
        server_address = ('', 80)
        httpd = HTTPServer(server_address, FocusHandler)
        print("⚡ Focus server running on http://127.0.0.1:80")
        httpd.serve_forever()
    except PermissionError:
        print("❌ Admin rights required to run server on port 80.")
    except Exception as e:
        print(f"An error occurred in focus server: {e}")

def start_focus_server():
    global server_thread
    if server_thread and server_thread.is_alive():
        print("Focus server already running.")
        return
    server_thread = threading.Thread(target=run_focus_server, daemon=True)
    server_thread.start()

def stop_focus_server():
    global httpd
    if httpd:
        httpd.shutdown()
        print("🛑 Focus server stopped.")
    else:
        print("Focus server not running.")

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    # Clean up previous data for consistent testing
    # Note: This will delete the shared DB file from the platform-specific data directory
    # Only uncomment if you want to completely reset the DB for testing block_controller
    # if os.path.exists(DB_FILE):
    #     os.remove(DB_FILE)

    print(f"Database will be stored at: {DB_FILE}")
    init_db() # Ensure DB structure is ready

    print("\n--- Testing Blocklist Operations ---")
    print("Adding example.com, facebook.com, and instagram.com to blocklist...")
    add_to_blocklist("example.com")
    add_to_blocklist("facebook.com")
    add_to_blocklist("instagram.com")
    add_to_blocklist("instagram.com") # Trying to add again (should be ignored due to UNIQUE)

    current_blocklist = get_blocklist()
    print(f"Current Blocklist: {current_blocklist}")

    print("\n--- Modifying Hosts File (Requires Admin Privileges) ---")
    print("Attempting to block sites from the list...")
    # NOTE: You'll need to run this script with administrator privileges
    # to modify the hosts file on Windows, or root privileges on Linux/macOS.
    try:
        block_sites()
        print("Sites should now be blocked. Try navigating to example.com in your browser.")
    except PermissionError:
        print("Permission denied: Cannot modify hosts file. Run as administrator/root.")
    except Exception as e:
        print(f"An error occurred: {e}")

    print("\n--- Starting Focus Server ---")
    start_focus_server()
    # Let the server run for a bit if you're testing manually
    import time
    # time.sleep(5) # Uncomment for manual testing to see server start

    print("\n--- Removing a site from blocklist ---")
    remove_from_blocklist("example.com")
    current_blocklist = get_blocklist()
    print(f"Blocklist after removing example.com: {current_blocklist}")

    print("\n--- Unblocking All Sites ---")
    # Again, requires admin privileges
    try:
        unblock_all()
        print("All sites should now be unblocked.")
    except PermissionError:
        print("Permission denied: Cannot modify hosts file. Run as administrator/root.")

    print("\n--- Stopping Focus Server ---")
    stop_focus_server()

    # Manual check: Verify hosts file contents after script runs
    # You can open C:\Windows\System32\drivers\etc\hosts (Windows) or /etc/hosts (Linux/macOS)
    # in a text editor to confirm changes.