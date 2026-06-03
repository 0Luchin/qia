#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import threading
import time
import random
import urllib.request
import urllib.error
from pathlib import Path

# --- CONFIGURACIÓN Y CONSTANTES ---
VERSION = "2.0.2"
CONFIG_DIR = Path.home() / ".config" / "qia"
LOG_DIR = Path.home() / ".local" / "share" / "qia" / "logs"
TIMEOUT_FILE = CONFIG_DIR / "timeout"
ACTIVITY_FILE = CONFIG_DIR / "last_activity"
DEFAULT_TIMEOUT_MINS = 30
PORT_FILE = CONFIG_DIR / "port"
MODEL_FILE = CONFIG_DIR / "model"
PROFILE_FILE = CONFIG_DIR / "profile"
COLOR_FILE = CONFIG_DIR / "color"

DEFAULT_MODEL = "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
DEFAULT_PROFILE = "terminal"

def get_timeout():
    if not TIMEOUT_FILE.exists(): TIMEOUT_FILE.write_text(str(DEFAULT_TIMEOUT_MINS) + "\n")
    try: return int(TIMEOUT_FILE.read_text().strip())
    except: return DEFAULT_TIMEOUT_MINS

def get_port():
    if not PORT_FILE.exists(): PORT_FILE.write_text("18080\n")
    return PORT_FILE.read_text().strip()

BACKEND_URL = f"http://127.0.0.1:{get_port()}"

# ANSI Colors
C_RESET = "\033[0m"
C_LIME = "\033[38;5;118m"
C_ORANGE = "\033[38;5;215m"
C_WHITE = "\033[97m"
C_GRAY = "\033[90m"
C_YELLOW = "\033[93m"
C_RED = "\033[31m"
C_CYAN = "\033[36m"
C_BLUE = "\033[34m"

# --- LOGOS ---
LOGO = r"""
@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@
@@@@@        @@@@@
@@@    @@@@    @@@
@@@   @@@@@@   @@@
@@@    @@@@    @@@
@@@@@          @@@
@@@@@@@@@@@@   @@@
@@@@@@@@@@@@   @@@
"""
LOGO_SMALL = ["@@@@@@@@@@", "@@@    @@@", "@@  @@  @@", "@@@     @@", "@@@@@@  @@"]

# --- CLASES DE APOYO ---

class QIAConfig:
    @staticmethod
    def ensure():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if not MODEL_FILE.exists(): MODEL_FILE.write_text(DEFAULT_MODEL + "\n")
        if not PROFILE_FILE.exists(): PROFILE_FILE.write_text(DEFAULT_PROFILE + "\n")
        if not COLOR_FILE.exists(): COLOR_FILE.write_text("on\n")
        if not ACTIVITY_FILE.exists(): ACTIVITY_FILE.write_text(str(time.time()))

    @staticmethod
    def get_model():
        QIAConfig.ensure()
        return MODEL_FILE.read_text().strip()

    @staticmethod
    def set_model(model):
        MODEL_FILE.write_text(model + "\n")

    @staticmethod
    def get_profile():
        return PROFILE_FILE.read_text().strip()

    @staticmethod
    def color_enabled():
        try: return COLOR_FILE.read_text().strip() != "off"
        except: return True

class QIAVisuals:
    @staticmethod
    def c(text, color):
        if not QIAConfig.color_enabled(): return str(text)
        return f"{color}{text}{C_RESET}"

    @staticmethod
    def animate_logo(stop_event, mode="q"):
        start_time = time.perf_counter()
        sys.stderr.write("\r\033[?25l") 
        logo = LOGO_SMALL
        block_lines = len(logo) + 1
        try:
            while not stop_event.is_set():
                elapsed = time.perf_counter() - start_time
                output = []
                for line in logo:
                    rendered_line = ""
                    for ch in line:
                        if ch == "@" and random.random() < 0.1: rendered_line += QIAVisuals.c("@", C_ORANGE)
                        else: rendered_line += QIAVisuals.c(ch, C_LIME)
                    output.append("\033[2K" + rendered_line)
                timer = QIAVisuals.c(f"{elapsed:04.1f}s", C_YELLOW).rjust(20)
                output.append("\033[2K" + timer)
                sys.stderr.write("\n".join(output) + "\n")
                sys.stderr.write(f"\033[{block_lines}F")
                sys.stderr.flush()
                time.sleep(0.1)
        finally:
            sys.stderr.write("\033[J\033[?25h")
            sys.stderr.flush()

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

    @staticmethod
    def ensure():
        if QIABackend.is_ready():
            ACTIVITY_FILE.write_text(str(time.time()))
            return True
        
        model = QIAConfig.get_model()
        server_bin = Path.home() / "local-llm" / "llama.cpp" / "build" / "bin" / "llama-server"
        model_path = Path.home() / "local-llm" / "models" / "qwen2.5-coder-3b" / model

        if not server_bin.exists():
            print(QIAVisuals.c(f"Error: llama-server no encontrado en {server_bin}", C_RED))
            sys.exit(1)
        
        if not model_path.exists():
            default_path = Path.home() / "local-llm" / "models" / "qwen2.5-coder-3b" / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
            if default_path.exists(): model_path = default_path
            else:
                print(QIAVisuals.c(f"Error: Modelo no encontrado en {model_path}", C_RED))
                sys.exit(1)

        log_file = open(LOG_DIR / "llama-server.log", "a")
        subprocess.Popen(
            [str(server_bin), "-m", str(model_path), "--port", get_port(), "--host", "127.0.0.1", "-c", "2048"],
            stdout=log_file, stderr=subprocess.STDOUT, start_new_session=True
        )
        QIABackend.start_watcher()
        
        start = time.time()
        while time.time() - start < 30:
            if QIABackend.is_ready(): return True
            time.sleep(0.5)
        return False

# --- LÓGICA DE PROMPT ---
PROFILES = {
    "terminal": "Asistente experto en Linux, Bash y Python. Respuestas breves y técnicas.",
    "noc": "Especialista en redes e infraestructura. Diagnóstico y seguridad.",
    "python": "Experto senior en Python. Código limpio y eficiente.",
}

def get_system_prompt(mode):
    profile_text = PROFILES.get(QIAConfig.get_profile(), PROFILES["terminal"])
    if mode == "qdo":
        return f"{profile_text}\nEres qdo, un sintetizador de comandos Bash. TU ÚNICA SALIDA DEBE SER EL COMANDO BASH EJECUTABLE.\nREGLAS ESTRICTAS: NO markdown, NO explicaciones, NO saludos. Si pide crear archivo, usa cat << 'EOF' > archivo ... EOF."
    elif mode == "qcode":
        return f"{profile_text}\nEres qcode, un generador de código puro. TU ÚNICA SALIDA DEBE SER EL CÓDIGO FUENTE.\nREGLAS: NO markdown, NO explicaciones, NO saludos."
    else:
        return f"{profile_text}\nRespuesta técnica directa, máximo 2 párrafos."

def query_llm(prompt, mode="q"):
    start_t = time.perf_counter()
    stop_event = threading.Event()
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo, args=(stop_event, mode))
    anim_thread.start()
    
    try: QIABackend.ensure()
    except Exception as e:
        stop_event.set(); anim_thread.join()
        print(QIAVisuals.c(f"\nError iniciando backend: {e}", C_RED)); sys.exit(1)
    
    payload = {"messages": [{"role": "system", "content": get_system_prompt(mode)}, {"role": "user", "content": prompt}], "stream": True, "temperature": 0.01 if mode == "qdo" else 0.2 if mode == "qcode" else 0.6}
    req = urllib.request.Request(f"{BACKEND_URL}/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    
    full_response = ""
    first_token = True
    is_filtering = (mode in ("qdo", "qcode"))
    display_buffer = ""
    
    try:
        with urllib.request.urlopen(req) as response:
            for line in response:
                line = line.decode().strip()
                if not line or line == "data: [DONE]": continue
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        token = data["choices"][0]["delta"].get("content", "")
                    except: continue
                    if token:
                        if first_token:
                            stop_event.set(); anim_thread.join()
                            label = "Comando Propuesto:" if mode == "qdo" else "Código Generado:" if mode == "qcode" else ""
                            if label: sys.stdout.write(f"{QIAVisuals.c(label, C_YELLOW if mode == 'qdo' else C_LIME)}\n")
                            sys.stdout.flush(); first_token = False
                        full_response += token
                        if is_filtering:
                            display_buffer += token
                            if "```" in display_buffer:
                                if "\n" in display_buffer:
                                    remaining = display_buffer.split("\n", 1)[1]
                                    if remaining: sys.stdout.write(remaining)
                                    display_buffer = ""; is_filtering = False
                                continue
                            elif len(display_buffer) > 20:
                                sys.stdout.write(display_buffer); display_buffer = ""; is_filtering = False
                        else:
                            clean_token = token.replace("```", "").replace("`", "")
                            if mode == "qdo": clean_token = clean_token.replace("$ ", "")
                            sys.stdout.write(clean_token)
                        sys.stdout.flush()
    except Exception as e:
        stop_event.set(); anim_thread.join(); print(f"\nError: {e}"); sys.exit(1)
        
    if display_buffer and is_filtering:
        sys.stdout.write(display_buffer); sys.stdout.flush()
    sys.stdout.write("\n") # Nueva línea después de respuesta
    return full_response.strip(), time.perf_counter() - start_t

# --- COMANDOS ---
def cmd_qia_install(): subprocess.run(["scripts/install.sh"])
def cmd_qia_status():
    print(f"{LOGO}\nQIA Version: {VERSION}\nBackend: {BACKEND_URL} [{'ACTIVO' if QIABackend.is_ready() else 'OFF'}]\nModelo: {QIAConfig.get_model()}\nPerfil: {QIAConfig.get_profile()}")
def cmd_qia_help():
    print(f"{LOGO}\nComandos: qia install, status, stop, timeout, help.\nHerramientas: q, qdo, qcode, qmodel, qprofile.")
def cmd_qia_model(args):
    model_dir = Path.home() / "local-llm" / "models" / "qwen2.5-coder-3b"
    if not args:
        print(QIAVisuals.c("\nModelos disponibles:", C_LIME))
        current = QIAConfig.get_model()
        if model_dir.exists():
            for f in model_dir.glob("*.gguf"):
                star = "*" if f.name == current else " "; print(f" {QIAVisuals.c(star, C_YELLOW)} {f.name}")
        print(f"\nUso: qmodel <nombre_archivo>")
        return
    new_model = args[0]
    if (model_dir / new_model).exists():
        QIAConfig.set_model(new_model)
        print(QIAVisuals.c(f"✔ Modelo cambiado a: {new_model}", C_LIME))
    else: print(QIAVisuals.c(f"Error: Modelo no existe.", C_RED))
def cmd_qia_profile(args):
    if not args:
        print(QIAVisuals.c("\nPerfiles disponibles:", C_LIME))
        current = QIAConfig.get_profile()
        for p in PROFILES:
            star = "*" if p == current else " "; print(f" {QIAVisuals.c(star, C_YELLOW)} {p.ljust(10)} {QIAVisuals.c(PROFILES[p], C_GRAY)}")
        print(f"\nUso: qprofile <nombre>")
        return
    new_profile = args[0]
    if new_profile in PROFILES:
        PROFILE_FILE.write_text(new_profile + "\n")
        print(QIAVisuals.c(f"✔ Perfil cambiado a: {new_profile}", C_LIME))
    else: print(QIAVisuals.c(f"Error: Perfil no reconocido.", C_RED))

def handle_qdo(prompt):
    while True:
        answer, elapsed = query_llm(prompt, mode="qdo")
        blocks = re.findall(r"```(?:bash|sh)?\n?(.*?)```", answer, re.DOTALL)
        clean_cmd = blocks[0].strip() if blocks else answer.strip()
        clean_cmd = clean_cmd.replace("`", "").strip()
        print(f"\n{QIAVisuals.c(f'# Tiempo: {elapsed:.2f}s', C_GRAY)}")
        print("-" * 30) # Separación visual
        choice = input(f"\n{QIAVisuals.c('[E]', C_LIME)}jecutar / {QIAVisuals.c('[R]', C_YELLOW)}efinar / {QIAVisuals.c('[X]', C_BLUE)}plicar / {QIAVisuals.c('[C]', C_RED)}ancelar? ").lower()
        if choice == 'e': subprocess.run(clean_cmd, shell=True); return
        elif choice == 'r': prompt = f"Comando anterior: {clean_cmd}\nAjuste pedido: {input('Ajuste: ')}\nGenera comando bash plano."; continue
        elif choice == 'x':
            print(f"\n{QIAVisuals.c('Explicación:', C_BLUE)}")
            # We call with mode="q" explicitly to avoid the "Comando Propuesto" label
            query_llm(f"Explica esto: {clean_cmd}", mode="q")
            continue
        else: return

def handle_qcode(prompt):
    while True:
        answer, elapsed = query_llm(prompt, mode="qcode")
        blocks = re.findall(r"```[a-zA-Z]*\n?(.*?)```", answer, re.DOTALL)
        clean_code = blocks[0].strip() if blocks else answer.strip()
        print(f"\n{QIAVisuals.c(f'# Tiempo: {elapsed:.2f}s', C_GRAY)}")
        print("-" * 30) # Separación visual
        choice = input(f"\n{QIAVisuals.c('[G]', C_LIME)}uardar / {QIAVisuals.c('[R]', C_YELLOW)}efinar / {QIAVisuals.c('[X]', C_BLUE)}plicar / {QIAVisuals.c('[C]', C_RED)}ancelar? ").lower()
        if choice == 'g':
            path = input("Ruta (ej: codigo.py): ") or "codigo.py"; Path(path).write_text(clean_code); print("✔ Guardado."); return
        elif choice == 'r': prompt = f"Código:\n{clean_code}\nAjuste: {input('Ajuste: ')}\nGenera código nuevo."; continue
        elif choice == 'x': query_llm(f"Explica este código: {clean_code}", mode="q"); continue
        else: return

# --- MAIN ---
def main():
    QIAConfig.ensure()
    invoked = os.environ.get("QIA_INVOKED_AS") or Path(sys.argv[0]).name
    args = sys.argv[1:]
    
    if invoked == "qia":
        sub = args[0] if args else "help"
        if sub == "install": cmd_qia_install()
        elif sub == "status": cmd_qia_status()
        elif sub == "stop": QIABackend.stop()
        elif sub == "help": cmd_qia_help()
    elif invoked == "qmodel": cmd_qia_model(args)
    elif invoked == "qprofile": cmd_qia_profile(args)
    elif not args: cmd_qia_help()
    elif invoked == "qdo": handle_qdo(" ".join(args))
    elif invoked == "qcode": handle_qcode(" ".join(args))
    else: query_llm(" ".join(args), mode="q")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.exit(0)
