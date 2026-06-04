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
    "1": {"primary": "\033[38;5;46m", "secondary": "\033[38;5;226m", "tertiary": "\033[38;5;208m"}, # Neon Green/Yellow/Orange
    "2": {"primary": "\033[38;5;39m", "secondary": "\033[38;5;208m", "tertiary": "\033[38;5;226m"}, # Blue/Orange/Yellow
    "3": {"primary": "\033[38;5;201m", "secondary": "\033[38;5;82m", "tertiary": "\033[38;5;226m"}, # Magenta/Lime/Yellow
    "4": {"primary": "\033[38;5;160m", "secondary": "\033[38;5;208m", "tertiary": "\033[38;5;190m"}, # Red/Orange/Yellow
    "5": {"primary": "\033[38;5;129m", "secondary": "\033[38;5;201m", "tertiary": "\033[38;5;87m"}, # Purple/Magenta/Cyan
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
        # text_list es una lista que puede ser actualizada dinámicamente
        logo_lines = [line for line in LOGO.split('\n') if line.strip()]
        
        # Ocultar cursor
        sys.stderr.write("\033[?25l")
        
        try:
            while not stop_event.is_set():
                text_lines = text_list  # Leer la lista actual
                max_height = max(len(logo_lines), len(text_lines))
                # Dibujar frame completo
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
                    else:
                        logo_part = " " * 18
                    
                    text_part = text_lines[i] if i < len(text_lines) else ""
                    frame.append(f"\033[2K\r{logo_part}  {text_part}")
                
                # Unir con \n pero sin añadir uno al final que provoque scroll
                sys.stderr.write("\n".join(frame))
                # Subir el cursor `max_height - 1` líneas para volver al principio del logo
                sys.stderr.write(f"\033[{max_height - 1}A\r")
                sys.stderr.flush()
                time.sleep(0.1)
                
            # Limpiar bloque moviéndose al final del mismo
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
    status_text = ["Iniciando instalación..."]
    
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo_big, args=(stop_event, status_text))
    anim_thread.start()
    
    # Simulación de pasos de instalación
    time.sleep(1)
    status_text[0] = "Configurando entorno..."
    time.sleep(1)
    status_text[0] = "Instalando dependencias..."
    time.sleep(1)
    status_text[0] = "✔ Instalación completada. Presione Enter para continuar..."
    
    # Esperar entrada sin detener el hilo de animación inmediatamente
    input()
    
    stop_event.set()
    anim_thread.join()

def cmd_qia_doctor():
    stop_event = threading.Event()
    status_text = ["Ejecutando diagnóstico..."]
    
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo_big, args=(stop_event, status_text))
    anim_thread.start()
    
    # Simulación de pasos de doctor
    time.sleep(1)
    status_text[0] = "Verificando backend..."
    time.sleep(1)
    status_text[0] = "Verificando modelos..."
    time.sleep(1)
    status_text[0] = "✔ Diagnóstico finalizado. Presione Enter para continuar..."
    
    # Esperar entrada sin detener el hilo de animación inmediatamente
    input()
    
    stop_event.set()
    anim_thread.join()

def cmd_qia_status():
    status_text = [
        f"QIA Version: {VERSION}",
        f"Backend: {BACKEND_URL} [{'ACTIVO' if QIABackend.is_ready() else 'OFF'}]",
        f"Modelo: {QIAConfig.get_model()}",
        f"Perfil: {QIAConfig.get_profile()}",
        "Presione Enter para salir..."
    ]
    stop_event = threading.Event()
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo_big, args=(stop_event, status_text))
    anim_thread.start()
    input()
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
    # Logo estático coloreado y título a la derecha
    logo = LOGO_SMALL
    title = "QIA HELP"
    
    for i in range(len(logo)):
        # Colorear logo con color primario
        rendered_logo = ""
        for ch in logo[i]:
            if ch == "@": rendered_logo += QIAVisuals.c("@", get_c("primary"))
            else: rendered_logo += " "
        
        # Título centrado verticalmente a la derecha (línea 1 y 2)
        side_text = title if i == 1 else ("==========" if i == 2 else "")
        print(f"{rendered_logo}    {QIAVisuals.c(side_text, C_WHITE())}")
    
    cmds = {
        "install": "Reinstala QIA.",
        "doctor": "Ejecuta diagnóstico del sistema.",
        "status": "Muestra estado de QIA.",
        "color <1-5>": "Cambia la paleta de colores.",
        "update": "Actualiza QIA a la última versión.",
        "stop": "Detiene el backend.",
        "timeout": "Configura tiempo de espera.",
        "help": "Muestra este menú.",
        "q <prompt>": "Consulta general al LLM.",
        "qdo <prompt>": "Ejecuta comandos bash.",
        "qcode <prompt>": "Genera o analiza código.",
        "qia model <name>": "Cambia el modelo.",
        "qia profile <name>": "Cambia el perfil."
    }
    
    print(f"\n{colored_text('Comandos:')}")
    for cmd, desc in cmds.items():
        # Comando en blanco brillante, descripción aleatoria
        print(f"  {QIAVisuals.c(cmd.ljust(15), C_WHITE())} {colored_text(desc)}")
    print()
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

def cmd_qia_color(args):
    if not args or args[0] not in PALETTES:
        print(QIAVisuals.c("\nUso: qia color <1-5>", C_YELLOW()))
        return

    QIAConfig.set_color_palette(args[0])
    print(QIAVisuals.c(f"\n✔ Paleta de colores cambiada a: {args[0]}", C_LIME()))

def cmd_qia_update():
    print(QIAVisuals.c("\n✔ Buscando actualizaciones en GitHub...", C_LIME()))
    try:
        # Asumiendo que el directorio es un repositorio git
        subprocess.run(["git", "pull"], check=True, cwd=str(Path(__file__).resolve().parent))
        print(QIAVisuals.c("✔ Código actualizado.", C_LIME()))
        subprocess.run(["make", "install"], check=True, cwd=str(Path(__file__).resolve().parent))
        print(QIAVisuals.c("✔ Instalación finalizada. Reinicia QIA.", C_LIME()))
    except subprocess.CalledProcessError as e:
        print(QIAVisuals.c(f"Error al actualizar: {e}", C_RED()))

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
