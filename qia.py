#!/usr/bin/env python3
import json, os, re, subprocess, sys, threading, time, random, urllib.request, urllib.error
from pathlib import Path

# --- CONFIGURACIÓN ---
CONFIG_DIR = Path.home() / ".config" / "qia"
LOG_DIR = Path.home() / ".local" / "share" / "qia" / "logs"
TIMEOUT_FILE = CONFIG_DIR / "timeout"
ACTIVITY_FILE = CONFIG_DIR / "last_activity"
DEFAULT_TIMEOUT_MINS = 30
PORT_FILE = CONFIG_DIR / "port"

def get_timeout():
    if not TIMEOUT_FILE.exists(): TIMEOUT_FILE.write_text(str(DEFAULT_TIMEOUT_MINS) + "\n")
    try: return int(TIMEOUT_FILE.read_text().strip())
    except: return DEFAULT_TIMEOUT_MINS

def get_port():
    if not PORT_FILE.exists(): PORT_FILE.write_text("18080\n")
    return PORT_FILE.read_text().strip()

BACKEND_URL = f"http://127.0.0.1:{get_port()}"

# --- BACKEND ---
class QIABackend:
    @staticmethod
    def is_ready():
        try:
            with urllib.request.urlopen(f"{BACKEND_URL}/v1/models", timeout=1.5) as r: return r.status == 200
        except: return False
    
    @staticmethod
    def stop():
        subprocess.run(["pkill", "-f", "llama-server"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", "qia_watcher"], stderr=subprocess.DEVNULL)

    @staticmethod
    def start_watcher():
        subprocess.run(["pkill", "-f", "qia_watcher"], stderr=subprocess.DEVNULL)
        watcher_code = f"""
import time, subprocess, sys
from pathlib import Path
activity_file = Path("{ACTIVITY_FILE}")
timeout_file = Path("{TIMEOUT_FILE}")
def get_t():
    try: return int(timeout_file.read_text().strip()) * 60
    except: return {DEFAULT_TIMEOUT_MINS} * 60
while True:
    time.sleep(60)
    try:
        if time.time() - float(activity_file.read_text()) > get_t():
            subprocess.run(["pkill", "-f", "llama-server"], stderr=subprocess.DEVNULL)
            sys.exit(0)
    except: pass
"""
        subprocess.Popen([sys.executable, "-c", watcher_code, "qia_watcher"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

# --- COMANDOS ---
def cmd_qia_install():
    bin_dir = Path.home() / "bin"
    bin_dir.mkdir(exist_ok=True)
    self_path = Path(__file__).resolve()
    for t in ["q", "qcode", "qia", "qmodel", "qprofile"]:
        t_path = bin_dir / t
        if t_path.exists(): t_path.unlink()
        os.symlink(self_path, t_path)
    qdo = bin_dir / "qdo"
    qdo.write_text(f"#!/usr/bin/env bash\nQIA_INVOKED_AS=qdo python3 {self_path} \"$@\"\n")
    qdo.chmod(0o755)
    print("--- INSTALACIÓN COMPLETADA ---")

def cmd_qia_status():
    def get_link(text, url): return f"\033]8;;{url}\033\\{text}\t{url}\033]8;;\033\\"
    links = [get_link("🔗 LARLAB", "https://larlab.xyz"), get_link("🔗 GitHub", "https://github.com/0Luchin/qia"), get_link("☕ Support Me!", "https://www.paypal.com/paypalme/0Luchin")]
    print(f"Backend: [{'ACTIVO' if QIABackend.is_ready() else 'OFF'}]")
    print(f"Timeout: {get_timeout()} min")
    for l in links: print(l)

def main():
    if not CONFIG_DIR.exists(): CONFIG_DIR.mkdir(parents=True)
    if not ACTIVITY_FILE.exists(): ACTIVITY_FILE.write_text(str(time.time()))
    
    args = sys.argv[1:]
    invoked = os.environ.get("QIA_INVOKED_AS") or Path(sys.argv[0]).name
    
    if invoked == "qia":
        sub = args[0] if args else "help"
        if sub == "install": cmd_qia_install()
        elif sub == "status": cmd_qia_status()
        elif sub == "stop": QIABackend.stop()
        elif sub == "timeout":
            if not args[1:]: print(f"Timeout: {get_timeout()} min"); return
            TIMEOUT_FILE.write_text(str(int(args[1])) + "\n")
            print(f"✔ Timeout: {args[1]} min")
        return

if __name__ == "__main__":
    main()
