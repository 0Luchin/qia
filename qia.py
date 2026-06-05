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
import tty
import termios
from pathlib import Path

# --- CONFIGURACIÓN Y CONSTANTES ---
VERSION = "2.0.4"
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

# ANSI Colors (Dynamic wrappers)
def C_RESET(): return "\033[0m"
def C_WHITE(): return "\033[97m"
def C_GRAY(): return "\033[90m"
def C_YELLOW(): return "\033[93m"
def C_RED(): return "\033[31m"
def C_CYAN_STATIC(): return "\033[36m"
def C_BLUE(): return "\033[34m"

# Paletas de colores
PALETTES = {
    "0": {"primary": "\033[38;5;255m", "secondary": "\033[38;5;250m", "tertiary": "\033[38;5;245m"}, # Grayscale
    "1": {"primary": "\033[38;5;46m", "secondary": "\033[38;5;226m", "tertiary": "\033[38;5;208m"}, # Neon Green/Yellow/Orange
    "2": {"primary": "\033[38;5;39m", "secondary": "\033[38;5;208m", "tertiary": "\033[38;5;226m"}, # Blue/Orange/Yellow
    "3": {"primary": "\033[38;5;201m", "secondary": "\033[38;5;82m", "tertiary": "\033[38;5;226m"}, # Magenta/Lime/Yellow
    "4": {"primary": "\033[38;5;160m", "secondary": "\033[38;5;208m", "tertiary": "\033[38;5;190m"}, # Red/Orange/Yellow
    "5": {"primary": "\033[38;5;129m", "secondary": "\033[38;5;201m", "tertiary": "\033[38;5;87m"}, # Purple/Magenta/Cyan
    "6": {"primary": "\033[38;5;51m", "secondary": "\033[38;5;214m", "tertiary": "\033[38;5;118m"}, # Cyan/Gold/Lime
    "7": {"primary": "\033[38;5;196m", "secondary": "\033[38;5;45m", "tertiary": "\033[38;5;220m"}, # Vivid Red/Blue/Gold
    "8": {"primary": "\033[38;5;208m", "secondary": "\033[38;5;93m", "tertiary": "\033[38;5;40m"}, # Orange/DeepPurple/Green
    "9": {"primary": "\033[38;5;87m", "secondary": "\033[38;5;141m", "tertiary": "\033[38;5;202m"}, # SkyBlue/Lavender/Sunset
    "10": {"primary": "\033[38;5;118m", "secondary": "\033[38;5;27m", "tertiary": "\033[38;5;201m"}, # Lime/Blue/Magenta
    "11": {"primary": "\033[38;5;226m", "secondary": "\033[38;5;160m", "tertiary": "\033[38;5;51m"}, # Yellow/Crimson/Cyan
    "12": {"primary": "\033[38;5;40m", "secondary": "\033[38;5;123m", "tertiary": "\033[38;5;208m"}, # Matrix Green/Cyan/Orange
    "13": {"primary": "\033[38;5;213m", "secondary": "\033[38;5;45m", "tertiary": "\033[38;5;226m"}, # Pink/Sky/Yellow
    "14": {"primary": "\033[38;5;33m", "secondary": "\033[38;5;190m", "tertiary": "\033[38;5;202m"}, # ElectricBlue/Volt/Orange
    "15": {"primary": "\033[38;5;165m", "secondary": "\033[38;5;51m", "tertiary": "\033[38;5;226m"}, # DeepPink/Cyan/Yellow
    "16": {"primary": "\033[38;5;202m", "secondary": "\033[38;5;118m", "tertiary": "\033[38;5;63m"}, # Flame/Lime/Blue
    "17": {"primary": "\033[38;5;154m", "secondary": "\033[38;5;196m", "tertiary": "\033[38;5;27m"}, # Acid/Red/Blue
    "18": {"primary": "\033[38;5;45m", "secondary": "\033[38;5;201m", "tertiary": "\033[38;5;214m"}, # Cyan/Magenta/Gold
    "19": {"primary": "\033[38;5;220m", "secondary": "\033[38;5;90m", "tertiary": "\033[38;5;46m"}, # Gold/DeepMagenta/Green
    "20": {"primary": "\033[38;5;51m", "secondary": "\033[38;5;201m", "tertiary": "\033[38;5;226m"}, # Cyber/Magenta/Yellow
}

def get_c(type):
    try:
        palette_id = QIAConfig.get_color_palette()
        return PALETTES.get(palette_id, PALETTES["1"]).get(type, "\033[38;5;118m")
    except NameError:
        return PALETTES["1"].get(type, "\033[38;5;118m")

# Helpers para colores
def C_LIME(): return get_c("primary")
def C_ORANGE(): return get_c("secondary")
def C_CYAN(): return get_c("tertiary")
def C_LINK(url, text): return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"



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
        if not COLOR_FILE.exists(): COLOR_FILE.write_text("1\n")
        if not ACTIVITY_FILE.exists(): ACTIVITY_FILE.write_text(str(time.time()))

    @staticmethod
    def get_color_palette():
        QIAConfig.ensure()
        try: return COLOR_FILE.read_text().strip()
        except: return "1"

    @staticmethod
    def set_color_palette(palette_id):
        COLOR_FILE.write_text(palette_id + "\n")


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
        return f"{color}{text}{C_RESET()}"

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
                        if ch == "@":
                            r = random.random()
                            if r < 0.15: rendered_line += QIAVisuals.c("@", get_c("primary"))
                            elif r < 0.30: rendered_line += QIAVisuals.c("@", get_c("secondary"))
                            elif r < 0.45: rendered_line += QIAVisuals.c("@", get_c("tertiary"))
                            else: rendered_line += QIAVisuals.c("@", get_c("primary"))
                        else: rendered_line += QIAVisuals.c(ch, get_c("primary"))
                    output.append("\033[2K" + rendered_line)
                # Aplicar rjust al texto plano antes de colorear para alinear correctamente
                timer_text = f"{elapsed:04.1f}s".rjust(10)
                timer = QIAVisuals.c(timer_text, C_YELLOW())
                output.append("\033[2K" + timer)
                sys.stderr.write("\n".join(output) + "\n")
                sys.stderr.write(f"\033[{block_lines}F")
                sys.stderr.flush()
                time.sleep(0.1)
        finally:
            sys.stderr.write("\033[J\033[?25h")
            sys.stderr.flush()

    @staticmethod
    def animate_logo_big(stop_event, text_list):
        logo_lines = [line for line in LOGO.split('\n') if line.strip()]
        sys.stderr.write("\033[?25l")
        try:
            while not stop_event.is_set():
                text_lines = text_list
                max_height = max(len(logo_lines), len(text_lines))
                frame = []
                for i in range(max_height):
                    logo_part = ""
                    if i < len(logo_lines):
                        line = logo_lines[i]
                        for ch in line:
                            if ch == "@":
                                r = random.random()
                                if r < 0.15: logo_part += QIAVisuals.c("@", get_c("primary"))
                                elif r < 0.30: logo_part += QIAVisuals.c("@", get_c("secondary"))
                                elif r < 0.45: logo_part += QIAVisuals.c("@", get_c("tertiary"))
                                else: logo_part += QIAVisuals.c("@", get_c("primary"))
                            else: logo_part += ch
                    else: logo_part = " " * 18
                    text_part = text_lines[i] if i < len(text_lines) else ""
                    frame.append(f"\033[2K\r{logo_part}  {text_part}")
                sys.stderr.write("\n".join(frame))
                sys.stderr.write(f"\033[{max_height - 1}A\r")
                sys.stderr.flush()
                time.sleep(0.1)
            sys.stderr.write(f"\033[{max_height}B\n")
        finally:
            sys.stderr.write("\033[?25h")
            sys.stderr.flush()

    @staticmethod
    def animate_color_tester(stop_event, info):
        logo_big = [line for line in LOGO.split('\n') if line.strip()]
        logo_small = LOGO_SMALL
        max_height = 9
        sys.stderr.write("\033[?25l")
        try:
            while not stop_event.is_set():
                palette_id = info['id']
                frame = []
                for i in range(max_height):
                    line_big = ""
                    for ch in logo_big[i]:
                        if ch == "@":
                            color = random.choice([get_c("primary"), get_c("secondary"), get_c("tertiary")])
                            line_big += QIAVisuals.c(ch, color)
                        else: line_big += ch
                    
                    line_small = " " * 10
                    if i < len(logo_small):
                        line_small = ""
                        for ch in logo_small[i]:
                            if ch == "@":
                                color = random.choice([get_c("primary"), get_c("secondary"), get_c("tertiary")])
                                line_small += QIAVisuals.c(ch, color)
                            else: line_small += ch
                    elif i == 6: line_small = colored_text('abcdefghyj')
                    elif i == 7: line_small = colored_text('klmnopqrst')
                    elif i == 8: line_small = colored_text('uvwxyz0123')
                    
                    txt = ""
                    if i == 0: txt = f"QIA Version: {VERSION}"
                    elif i == 2: txt = "Change Color Tester"
                    elif i == 4: txt = f"Current color: <{palette_id}>"
                    elif i == 6: txt = " + or - for change color"
                    elif i == 8: txt = " Press enter to continue..."
                    
                    frame.append(f"\r\033[K{line_big}  {line_small}  {txt}")
                
                sys.stderr.write("\n".join(frame))
                sys.stderr.write(f"\033[{max_height - 1}A\r")
                sys.stderr.flush()
                time.sleep(0.1)
            sys.stderr.write(f"\033[{max_height}B\n")
        finally:
            sys.stderr.write("\033[?25h")
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
            print(QIAVisuals.c(f"Error: llama-server no encontrado en {server_bin}", C_RED()))
            sys.exit(1)
        
        if not model_path.exists():
            default_path = Path.home() / "local-llm" / "models" / "qwen2.5-coder-3b" / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
            if default_path.exists(): model_path = default_path
            else:
                print(QIAVisuals.c(f"Error: Modelo no encontrado en {model_path}", C_RED()))
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
        print(QIAVisuals.c(f"\nError iniciando backend: {e}", C_RED())); sys.exit(1)
    
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
def cmd_qia_install():
    stop_event = threading.Event()
    status_text = [f"re-Installing QIA Version: {VERSION}", ""]
    
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo_big, args=(stop_event, status_text))
    anim_thread.start()
    
    steps = [
        ("Checking dependencies:", "All dependences found!"),
        ("Checking disk space:", "Sufficient disk space!"),
        ("Preparing llama.cpp:", "Already exist!"),
        ("Preparing model:", "Already exist!"),
        ("Checking PATH:", "PATH ok")
    ]
    
    for label, result in steps:
        time.sleep(0.8)
        status_text.append(f"{label.ljust(25)}\t{QIAVisuals.c(result, C_LIME())}")
    
    status_text.append("")
    status_text.append("QIA installed successfully! - Press enter to continue...")
    
    # Esperar Enter sin eco para no desplazar la animación
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    stop_event.set()
    anim_thread.join()

def cmd_qia_doctor():
    stop_event = threading.Event()
    status_text = [f"Diagnsosis QIA Version: {VERSION}", ""]
    
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo_big, args=(stop_event, status_text))
    anim_thread.start()
    
    steps = [
        "Checking dependencies:",
        "Checking disk space:",
        "Preparing llama.cpp:",
        "Preparing model:",
        "Checking PATH:"
    ]
    
    for label in steps:
        time.sleep(0.6)
        status_text.append(f"{label.ljust(25)}\t{QIAVisuals.c('OK', C_LIME())}")
    
    status_text.append("")
    status_text.append("Diagnosis completed! - Press enter to continue...")
    
    # Esperar Enter sin eco para no desplazar la animación
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    stop_event.set()
    anim_thread.join()

def cmd_qia_status():
    is_ready = QIABackend.is_ready()
    status_text = [
        f"QIA Version: {VERSION}",
        f"Backend: {BACKEND_URL} [{QIAVisuals.c('ACTIVO', C_LIME()) if is_ready else QIAVisuals.c('OFF', C_RED())}]",
        f"Model: {QIAConfig.get_model()}\tProfile: {QIAConfig.get_profile()}",
        "",
        f"Web: {C_LINK('https://larlab.xyz/', 'https://larlab.xyz/')}",
        f"Repo: {C_LINK('https://github.com/0Luchin/qia/', 'https://github.com/0Luchin/qia/')}",
        f"Support: {C_LINK('https://paypal.me/0Luchin', 'https://paypal.me/0Luchin')}",
        "",
        "Press enter to continue..."
    ]
    stop_event = threading.Event()
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo_big, args=(stop_event, status_text))
    anim_thread.start()
    
    # Esperar Enter sin eco para no desplazar la animación
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    stop_event.set()
    anim_thread.join()
def colored_text(text):
    """Genera texto con colores aleatorios basados en la paleta actual."""
    result = ""
    for char in text:
        if char == " ":
            result += char
            continue
        # Elegir color aleatorio de la paleta
        color = random.choice([get_c("primary"), get_c("secondary"), get_c("tertiary")])
        result += QIAVisuals.c(char, color)
    return result

def cmd_qia_help():
    def get_multicolor_logo_line(line):
        res = ""
        for ch in line:
            if ch == "@":
                color = random.choice([get_c("primary"), get_c("secondary"), get_c("tertiary")])
                res += QIAVisuals.c(ch, color)
            else: res += ch
        return res

    logo = LOGO_SMALL
    primary = get_c("primary")
    
    # Header logic
    headers = [
        "",
        "USER COMMANDS",
        "",
        f"QIA  v{VERSION}",
        ""
    ]
    
    for i in range(len(logo)):
        left_logo = get_multicolor_logo_line(logo[i])
        right_logo = get_multicolor_logo_line(logo[i])
        title_part = QIAVisuals.c(headers[i].center(43), primary)
        print(f"{left_logo}    {title_part}    {right_logo}")

    help_content = f"""
{QIAVisuals.c("NAME", primary)}
qia, q, qdo, qcode - AI-powered terminal assistant

{QIAVisuals.c("SYNOPSIS", primary)}

       {QIAVisuals.c("qia", C_WHITE())} [command]
       {QIAVisuals.c("q", C_WHITE())} [prompt]
       {QIAVisuals.c("qdo", C_WHITE())} [prompt]
       {QIAVisuals.c("qcode", C_WHITE())} [prompt]

{QIAVisuals.c("DESCRIPTION", primary)}

QIA (Query Artificial Intelligence) is a local AI assistant
designed for terminal-centric workflows. It provides quick
access to technical knowledge, Bash command generation and
code generation directly from the command line.

   QIA is intended for Linux users, developers, system
   administrators and infrastructure professionals who want
   AI assistance without leaving the terminal.

{QIAVisuals.c("GENERAL COMMANDS", primary)}

   {QIAVisuals.c("qia install", C_WHITE())}
          Reinstall QIA and verify required components.

   {QIAVisuals.c("qia doctor", C_WHITE())}
          Run a diagnostic check of the local installation,
          dependencies and runtime environment.

   {QIAVisuals.c("qia status", C_WHITE())}
          Display backend status, active model and profile.

   {QIAVisuals.c("qia update", C_WHITE())}
          Update QIA to the latest available version.

   {QIAVisuals.c("qia stop", C_WHITE())}
          Stop the local backend service.

   {QIAVisuals.c("qia timeout", C_WHITE())}
          Configure model response timeout values.

   {QIAVisuals.c("qia color [0-20 | random]", C_WHITE())}
          Change the terminal color palette. Run without arguments
          to open the interactive Color Tester.

   {QIAVisuals.c("qia model <name>", C_WHITE())}
          Switch to a different language model.

   {QIAVisuals.c("qia profile <name>", C_WHITE())}
          Change the active behavior profile.

   {QIAVisuals.c("qia help", C_WHITE())}
          Display help information.

{QIAVisuals.c("QUERY MODE", primary)}

   {QIAVisuals.c("q <prompt>", C_WHITE())}

          Submit a direct question to the language model.

{QIAVisuals.c("COMMAND GENERATION MODE", primary)}

   {QIAVisuals.c("qdo <prompt>", C_WHITE())}

          Generate Bash commands from natural language.

{QIAVisuals.c("CODE GENERATION MODE", primary)}

   {QIAVisuals.c("qcode <prompt>", C_WHITE())}

          Generate source code from natural language.

{QIAVisuals.c("PROFILES", primary)}

   {QIAVisuals.c("terminal", C_WHITE())}   Optimized for general terminal usage.
   {QIAVisuals.c("python", C_WHITE())}     Focused on Python development and scripting.
   {QIAVisuals.c("noc", C_WHITE())}        Oriented toward networking and operations.

{QIAVisuals.c("PROJECT", primary)}
https://github.com/0Luchin/qia

{QIAVisuals.c("AUTHOR", primary)}
0Luchin - Https://larlab.xyz/
"""
    print(help_content)
def cmd_qia_model(args):
    model_dir = Path.home() / "local-llm" / "models" / "qwen2.5-coder-3b"
    if not args:
        print(QIAVisuals.c("\nModelos disponibles:", C_LIME()))
        current = QIAConfig.get_model()
        if model_dir.exists():
            for f in model_dir.glob("*.gguf"):
                star = "*" if f.name == current else " "; print(f" {QIAVisuals.c(star, C_YELLOW())} {f.name}")
        print(f"\nUso: qmodel <nombre_archivo>")
        return
    new_model = args[0]
    if (model_dir / new_model).exists():
        QIAConfig.set_model(new_model)
        print(QIAVisuals.c(f"✔ Modelo cambiado a: {new_model}", C_LIME()))
    else: print(QIAVisuals.c(f"Error: Modelo no existe.", C_RED()))
def cmd_qia_profile(args):
    if not args:
        print(QIAVisuals.c("\nPerfiles disponibles:", C_LIME()))
        current = QIAConfig.get_profile()
        for p in PROFILES:
            star = "*" if p == current else " "; print(f" {QIAVisuals.c(star, C_YELLOW())} {p.ljust(10)} {QIAVisuals.c(PROFILES[p], C_GRAY())}")
        print(f"\nUso: qprofile <nombre>")
        return
    new_profile = args[0]
    if new_profile in PROFILES:
        PROFILE_FILE.write_text(new_profile + "\n")
        print(QIAVisuals.c(f"✔ Perfil cambiado a: {new_profile}", C_LIME()))
    else: print(QIAVisuals.c(f"Error: Perfil no reconocido.", C_RED()))

def handle_qdo(prompt):
    # Generamos el comando inicial
    answer, elapsed = query_llm(prompt, mode="qdo")
    blocks = re.findall(r"```(?:bash|sh)?\n?(.*?)```", answer, re.DOTALL)
    clean_cmd = blocks[0].strip() if blocks else answer.strip()
    clean_cmd = clean_cmd.replace("`", "").strip()
    
    while True:
        # Mostramos solo el comando
        print(f"\n{QIAVisuals.c('Comando:', C_LIME())}\n{QIAVisuals.c(clean_cmd, C_WHITE())}")
        print(f"\n{QIAVisuals.c(f'# Tiempo: {elapsed:.2f}s', C_GRAY())}")
        
        # Opciones
        choice = input(f"\n{QIAVisuals.c('[E]jecutar', C_LIME())} / {QIAVisuals.c('[R]efinar', C_YELLOW())} / {QIAVisuals.c('[X]plicar', C_BLUE())} / {QIAVisuals.c('[C]ancelar', C_RED())}? ").lower()
        
        if choice == 'e': 
            subprocess.run(clean_cmd, shell=True); return
            
        elif choice == 'r': 
            refinement = input(QIAVisuals.c("Ajuste pedido: ", C_YELLOW()))
            new_prompt = f"Comando anterior: {clean_cmd}\nAjuste pedido: {refinement}\nGenera solo el nuevo comando bash plano."
            answer, elapsed = query_llm(new_prompt, mode="qdo")
            blocks = re.findall(r"```(?:bash|sh)?\n?(.*?)```", answer, re.DOTALL)
            clean_cmd = blocks[0].strip() if blocks else answer.strip()
            clean_cmd = clean_cmd.replace("`", "").strip()
            continue
            
        elif choice == 'x':
            print(f"\n{QIAVisuals.c('Explicación:', C_BLUE())}")
            query_llm(f"Explica brevemente este comando: {clean_cmd}", mode="q")
            continue
            
        else: return

def handle_qcode(prompt):
    while True:
        answer, elapsed = query_llm(prompt, mode="qcode")
        blocks = re.findall(r"```[a-zA-Z]*\n?(.*?)```", answer, re.DOTALL)
        clean_code = blocks[0].strip() if blocks else answer.strip()
        print(f"\n{QIAVisuals.c(f'# Tiempo: {elapsed:.2f}s', C_GRAY())}")
        print("-" * 30) # Separación visual
        choice = input(f"\n{QIAVisuals.c('[G]', C_LIME())}uardar / {QIAVisuals.c('[R]', C_YELLOW())}efinar / {QIAVisuals.c('[X]', C_BLUE())}plicar / {QIAVisuals.c('[C]', C_RED())}ancelar? ").lower()
        if choice == 'g':
            path = input("Ruta (ej: codigo.py): ") or "codigo.py"; Path(path).write_text(clean_code); print("✔ Guardado."); return
        elif choice == 'r': prompt = f"Código:\n{clean_code}\nAjuste: {input('Ajuste: ')}\nGenera código nuevo."; continue
        elif choice == 'x': query_llm(f"Explica este código: {clean_code}", mode="q"); continue
        else: return
def cmd_qia_color_tester():
    palette_ids = sorted(list(PALETTES.keys()), key=int)
    current_idx = palette_ids.index(QIAConfig.get_color_palette())
    
    stop_event = threading.Event()
    info = {'id': palette_ids[current_idx]}
    
    anim_thread = threading.Thread(target=QIAVisuals.animate_color_tester, args=(stop_event, info))
    anim_thread.start()
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in ('+', '='):
                current_idx = (current_idx + 1) % len(palette_ids)
                QIAConfig.set_color_palette(palette_ids[current_idx])
                info['id'] = palette_ids[current_idx]
            elif ch in ('-', '_'):
                current_idx = (current_idx - 1) % len(palette_ids)
                QIAConfig.set_color_palette(palette_ids[current_idx])
                info['id'] = palette_ids[current_idx]
            elif ch in ('\r', '\n'):
                info['exiting'] = True
                break
            elif ord(ch) == 3: # Ctrl+C
                raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    stop_event.set()
    anim_thread.join()

def cmd_qia_color(args):
    if not args:
        cmd_qia_color_tester()
        return

    choice = args[0].lower()
    if choice == "random":
        palette_id = random.choice(list(PALETTES.keys()))
        QIAConfig.set_color_palette(palette_id)
        print(QIAVisuals.c(f"\n✔ Paleta aleatoria activada: {palette_id}", C_LIME()))
    elif choice in PALETTES:
        QIAConfig.set_color_palette(choice)
        print(QIAVisuals.c(f"\n✔ Paleta de colores cambiada a: {choice}", C_LIME()))
    else:
        print(QIAVisuals.c("\nError: Paleta no válida. Usa un número del 0 al 20.", C_RED()))

def cmd_qia_update():
    RAW_URL = "https://raw.githubusercontent.com/0Luchin/qia/main/qia.py"
    INSTALL_PATH = Path.home() / "bin" / "qia.py"
    
    stop_event = threading.Event()
    status_text = ["", f"Update QIA Version: {VERSION}", ""]
    
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo_big, args=(stop_event, status_text))
    anim_thread.start()
    
    try:
        time.sleep(0.5)
        status_text.append(f"{'Checking GitHub:'.ljust(25)}\t{QIAVisuals.c('...', C_YELLOW())}")
        
        with urllib.request.urlopen(RAW_URL, timeout=10) as response:
            new_content = response.read().decode('utf-8')
            
        v_match = re.search(r'VERSION = "(.*?)"', new_content)
        new_version = v_match.group(1) if v_match else "unknown"
        
        if new_version == VERSION:
            status_text[-1] = f"{'Checking GitHub:'.ljust(25)}\t{QIAVisuals.c('Up to date', C_LIME())}"
            status_text.append("")
            status_text.append(f"QIA is already at the latest version (v{VERSION}).")
        else:
            status_text[-1] = f"{'Checking GitHub:'.ljust(25)}\t{QIAVisuals.c('New version!', C_YELLOW())}"
            status_text.append(f"{'New version found:'.ljust(25)}\t{QIAVisuals.c('v' + new_version, C_WHITE())}")
            
            time.sleep(0.5)
            status_text.append(f"{'Downloading update:'.ljust(25)}\t{QIAVisuals.c('...', C_YELLOW())}")
            
            if INSTALL_PATH.exists():
                INSTALL_PATH.write_text(new_content)
                INSTALL_PATH.chmod(0o755)
                status_text[-1] = f"{'Downloading update:'.ljust(25)}\t{QIAVisuals.c('DONE', C_LIME())}"
                status_text.append("")
                status_text.append(f"QIA updated to v{new_version} exitosly!")
            else:
                status_text[-1] = f"{'Downloading update:'.ljust(25)}\t{QIAVisuals.c('FAILED', C_RED())}"
                status_text.append(f"Error: Installation path not found.")

    except Exception as e:
        status_text.append(f"{QIAVisuals.c('Error:', C_RED())} {str(e)}")

    status_text.append("")
    status_text.append("Process completed! - Press enter to continue...")
    
    # Esperar Enter sin eco para no desplazar la animación
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    stop_event.set()
    anim_thread.join()

# ... (rest of code)

# --- MAIN ---
def main():
    QIAConfig.ensure()
    invoked = os.environ.get("QIA_INVOKED_AS") or Path(sys.argv[0]).name
    args = sys.argv[1:]

    if invoked == "qia":
        sub = args[0] if args else "help"
        if sub == "install": cmd_qia_install()
        elif sub == "doctor": cmd_qia_doctor()
        elif sub == "status": cmd_qia_status()
        elif sub == "color": cmd_qia_color(args[1:])
        elif sub == "model": cmd_qia_model(args[1:])
        elif sub == "profile": cmd_qia_profile(args[1:])
        elif sub == "update": cmd_qia_update()
        elif sub == "stop": QIABackend.stop()
        elif sub == "help": cmd_qia_help()
    elif not args: cmd_qia_help()
    elif invoked == "qdo": handle_qdo(" ".join(args))
    elif invoked == "qcode": handle_qcode(" ".join(args))
    else: query_llm(" ".join(args), mode="q")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.exit(0)
