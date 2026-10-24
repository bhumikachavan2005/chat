"""
One-Click Universal Local Launcher for Vinu 💝 × Bhuu 🎀 Private Archive
- 100% Private Localhost Execution (127.0.0.1:8765)
- Fully cross-compatible across all Windows laptops & Python versions (3.9 - 3.14+)
- Auto-installs missing dependencies with --user fallback
- Auto-initializes local SQLite database & FTS5 search
- Auto-populates chat if database is fresh (preserves source .txt untouched)
- Automatically opens default browser
"""

import os
import sys
import subprocess
import webbrowser
import threading
import time
import socket
import urllib.request

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def ensure_dependencies():
    """Silently ensure all required packages are present on any machine or Python version."""
    missing = []
    for mod in ["fastapi", "uvicorn", "argon2", "cryptography"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        print("=" * 68)
        print(" [*] Setting up required packages on this computer...")
        print("     Packages: FastAPI, Uvicorn, Argon2, Cryptography, Multipart")
        print("=" * 68)
        pkgs = ["fastapi", "uvicorn", "argon2-cffi", "cryptography", "python-multipart"]
        
        success = False
        # Try standard pip install
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + pkgs)
            success = True
        except Exception:
            pass

        # Try user-level install if standard fails
        if not success:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user"] + pkgs)
                success = True
            except Exception as e:
                print(f"[!] Package install warning: {e}")

        if success:
            print("[+] All dependencies installed and ready.\n")


ensure_dependencies()

import uvicorn
from backend.database import init_db, get_db_connection, bulk_insert_messages
from backend.parser.whatsapp_parser import parse_whatsapp_file


def bootstrap_database():
    """Ensure database schema is ready and ingest source chat export if fresh."""
    init_db()
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
    conn.close()

    candidate_files = [
        os.path.join(BASE_DIR, "WhatsApp Chat with Vinu💝🎀.txt"),
        os.path.join(BASE_DIR, "WhatsApp Chat with Vinu.txt")
    ]
    
    for f in os.listdir(BASE_DIR):
        if f.endswith(".txt") and "WhatsApp" in f and f not in [os.path.basename(c) for c in candidate_files]:
            candidate_files.append(os.path.join(BASE_DIR, f))

    source_file = next((cf for cf in candidate_files if os.path.exists(cf)), None)

    if count == 0:
        if source_file:
            print(f"[*] Fresh database detected. Parsing '{os.path.basename(source_file)}'...")
            parsed_msgs = parse_whatsapp_file(source_file)
            inserted = bulk_insert_messages(parsed_msgs)
            print(f"[+] Successfully imported and indexed {inserted:,} messages for Vinu & Bhuu.")
        else:
            print("[i] Database initialized (0 messages). You can import your WhatsApp .txt from Settings.")
    else:
        print(f"[+] Local database ready with {count:,} messages.")


def is_port_in_use(host: str, port: int) -> bool:
    """Check if a specific TCP port is currently open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def find_available_port(host: str, start_port: int = 8765, max_attempts: int = 10) -> int:
    """Find start_port or the next available port."""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(host, p):
            return p
    return start_port


def is_archive_already_running(url: str) -> bool:
    """Check if our own archive server is already running on the given URL."""
    try:
        req = urllib.request.Request(f"{url}/api/auth/status", headers={"User-Agent": "Archive-Launcher"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def open_browser_delayed(url: str, delay_seconds: float = 1.0):
    """Open default web browser after server initializes."""
    time.sleep(delay_seconds)
    webbrowser.open(url)


def main():
    host = "127.0.0.1"  # STRICTLY LOCALHOST ONLY
    default_port = 8765
    default_url = f"http://{host}:{default_port}"

    # Check if archive server is already running on default port
    if is_port_in_use(host, default_port) and is_archive_already_running(default_url):
        print("=" * 68)
        print("      [PRIVATE ARCHIVE] VINU & BHUU WHATSAPP STORY")
        print("=" * 68)
        print(f"[+] Archive is ALREADY actively running at: {default_url}")
        print("[*] Opening your web browser directly...")
        print("=" * 68)
        webbrowser.open(default_url)
        return

    port = find_available_port(host, default_port)
    url = f"http://{host}:{port}"

    print("=" * 68)
    print("      [PRIVATE ARCHIVE] VINU & BHUU WHATSAPP STORY")
    print("=" * 68)
    print("  [#] PRIVACY STATUS: 100% Offline & Local")
    print("  [#] BIND INTERFACE: 127.0.0.1 (NOT accessible from network)")
    print(f"  [#] LOCAL URL:      {url}")
    print("=" * 68)

    # Initialize data
    bootstrap_database()

    # Launch browser in separate thread
    threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    print(f"\n🚀 Starting local archive server on {url}... Press Ctrl+C to stop.")
    uvicorn.run("backend.main:app", host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
