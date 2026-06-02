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
VERSION = "2.0.0"
CONFIG_DIR = Path.home() / ".config" / "qia"
LOG_DIR = Path.home() / ".local" / "share" / "qia" / "logs"
MODEL_FILE = CONFIG_DIR / "model"
PROFILE_FILE = CONFIG_DIR / "profile"
SESSION_FILE = CONFIG_DIR / "session.json"
COLOR_FILE = CONFIG_DIR / "color"

DEFAULT_MODEL = "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
DEFAULT_PROFILE = "terminal"
BACKEND_URL = "http://127.0.0.1:8080"

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
LOGO_SMALL = [
    "@@@@@@@@@@",
    "@@@    @@@",
    "@@  @@  @@",
    "@@@     @@",
    "@@@@@@  @@",
]

LOGO_LARGE = [
    "@@@@@@@@@@@@@@@@@@",
    "@@@@@@@@@@@@@@@@@@",
    "@@@@@        @@@@@",
    "@@@    @@@@    @@@",
    "@@@   @@@@@@   @@@",
    "@@@    @@@@    @@@",
    "@@@@@          @@@",
    "@@@@@@@@@@@@   @@@",
    "@@@@@@@@@@@@   @@@",
]

# --- CLASES DE APOYO ---

class QIAConfig:
    @staticmethod
    def ensure():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if not MODEL_FILE.exists():
            MODEL_FILE.write_text(DEFAULT_MODEL + "\n")
        if not PROFILE_FILE.exists():
            PROFILE_FILE.write_text(DEFAULT_PROFILE + "\n")
        if not COLOR_FILE.exists():
            COLOR_FILE.write_text("on\n")

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
        try:
            return COLOR_FILE.read_text().strip() != "off"
        except:
            return True

class QIAVisuals:
    @staticmethod
    def c(text, color):
        if not QIAConfig.color_enabled(): return str(text)
        return f"{color}{text}{C_RESET}"

    @staticmethod
    def animate_logo(stop_event, mode="q"):
        start_time = time.perf_counter()
        # Ocultamos cursor y empezamos en la línea actual (ya bajada por la shell)
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
                        if ch == "@" and random.random() < 0.1:
                            rendered_line += QIAVisuals.c("@", C_ORANGE)
                        else:
                            rendered_line += QIAVisuals.c(ch, C_LIME)
                    output.append("\033[2K" + rendered_line)
                
                timer = QIAVisuals.c(f"{elapsed:04.1f}s", C_YELLOW).rjust(20)
                output.append("\033[2K" + timer)
                
                # Escribimos el bloque y volvemos arriba inmediatamente
                sys.stderr.write("\n".join(output) + "\n")
                sys.stderr.write(f"\033[{block_lines}F")
                sys.stderr.flush()
                
                time.sleep(0.1)
        finally:
            # Limpiamos todo el bloque hacia abajo y restauramos cursor
            sys.stderr.write("\033[J\033[?25h")
            sys.stderr.flush()

class QIABackend:
    @staticmethod
    def is_ready():
        try:
            with urllib.request.urlopen(f"{BACKEND_URL}/v1/models", timeout=1.5) as r:
                return r.status == 200
        except:
            return False

    @staticmethod
    def stop():
        subprocess.run(["pkill", "-f", "llama-server"], stderr=subprocess.DEVNULL)

    @staticmethod
    def ensure():
        if QIABackend.is_ready(): return True
        
        model = QIAConfig.get_model()
        # En LARLAB los modelos están en carpetas específicas según la investigación previa
        server_bin = Path.home() / "local-llm" / "llama.cpp" / "build" / "bin" / "llama-server"
        model_path = Path.home() / "local-llm" / "models" / "qwen2.5-coder-3b" / model

        if not server_bin.exists():
            print(QIAVisuals.c(f"Error: llama-server no encontrado en {server_bin}", C_RED))
            sys.exit(1)
        
        if not model_path.exists():
            # Si el modelo exacto no existe, intentamos el default hardcoded por si acaso
            default_path = Path.home() / "local-llm" / "models" / "qwen2.5-coder-3b" / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
            if default_path.exists():
                model_path = default_path
            else:
                print(QIAVisuals.c(f"Error: Modelo no encontrado en {model_path}", C_RED))
                sys.exit(1)

        log_file = open(LOG_DIR / "llama-server.log", "a")
        subprocess.Popen(
            [str(server_bin), "-m", str(model_path), "--port", "8080", "--host", "127.0.0.1", "-c", "2048"],
            stdout=log_file, stderr=subprocess.STDOUT, start_new_session=True
        )
        
        # Wait for readiness
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
        return f"{profile_text}\nEres qdo, un sintetizador de comandos Bash. TU ÚNICA SALIDA DEBE SER EL COMANDO BASH EJECUTABLE.\n" \
               "REGLAS ESTRICTAS:\n" \
               "- PROHIBIDO usar Markdown o backticks (```).\n" \
               "- PROHIBIDO explicar el comando.\n" \
               "- PROHIBIDO saludar o dar contexto.\n" \
               "- Si el usuario pide crear un archivo, usa: cat << 'EOF' > archivo ... EOF\n" \
               "EJEMPLO:\n" \
               "Usuario: busca archivos log mayores a 10mb\n" \
               "Salida: find . -name '*.log' -size +10M"
    elif mode == "qcode":
        return f"{profile_text}\nEres qcode, un generador de código puro. TU ÚNICA SALIDA DEBE SER EL CÓDIGO FUENTE.\n" \
               "REGLAS:\n" \
               "- PROHIBIDO usar Markdown o backticks (```).\n" \
               "- PROHIBIDO explicar el código o saludar.\n" \
               "- Empieza directamente con la primera línea de código.\n" \
               "EJEMPLO:\n" \
               "Usuario: funcion python para leer json\n" \
               "Salida: import json\ndef read_json(path):\n    with open(path) as f: return json.load(f)"
    else:
        return f"{profile_text}\nRespuesta técnica directa, máximo 2 párrafos."

def query_llm(prompt, mode="q"):
    start_t = time.perf_counter()
    
    stop_event = threading.Event()
    anim_thread = threading.Thread(target=QIAVisuals.animate_logo, args=(stop_event, mode))
    anim_thread.start()
    
    try:
        QIABackend.ensure()
    except Exception as e:
        stop_event.set()
        anim_thread.join()
        print(QIAVisuals.c(f"\nError iniciando backend: {e}", C_RED))
        sys.exit(1)
    
    system = get_system_prompt(mode)
    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "stream": True,
        "temperature": 0.01 if mode == "qdo" else 0.2 if mode == "qcode" else 0.6
    }
    
    req = urllib.request.Request(
        f"{BACKEND_URL}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    
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
                            stop_event.set()
                            anim_thread.join()
                            
                            label = "Comando Propuesto:" if mode == "qdo" else "Código Generado:" if mode == "qcode" else ""
                            if label:
                                sys.stdout.write(f"{QIAVisuals.c(label, C_YELLOW if mode == 'qdo' else C_LIME)}\n")
                            sys.stdout.flush()
                            first_token = False
                        
                        full_response += token
                        
                        if is_filtering:
                            display_buffer += token
                            # Detectar valla inicial markdown
                            if "```" in display_buffer:
                                if "\n" in display_buffer:
                                    remaining = display_buffer.split("\n", 1)[1]
                                    if remaining: sys.stdout.write(remaining)
                                    display_buffer = ""
                                    is_filtering = False
                                continue
                            elif len(display_buffer) > 20:
                                sys.stdout.write(display_buffer)
                                display_buffer = ""
                                is_filtering = False
                        else:
                            clean_token = token.replace("```", "").replace("`", "")
                            if mode == "qdo": clean_token = clean_token.replace("$ ", "")
                            sys.stdout.write(clean_token)
                        
                        sys.stdout.flush()
    except Exception as e:
        stop_event.set()
        anim_thread.join()
        print(f"\nError de comunicación: {e}")
        sys.exit(1)
        
    if display_buffer and is_filtering:
        sys.stdout.write(display_buffer)
        sys.stdout.flush()

    elapsed = time.perf_counter() - start_t
    return full_response.strip(), elapsed

# --- COMANDOS ---

def cmd_qia_install():
    print(QIAVisuals.c("\n--- INSTALACIÓN QIA v2 ---", C_LIME))
    bin_dir = Path.home() / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    self_path = Path(__file__).resolve()
    
    targets = ["q", "qcode", "qia", "qmodel", "qprofile"]
    for t in targets:
        t_path = bin_dir / t
        if t_path.exists(): t_path.unlink()
        os.symlink(self_path, t_path)
        print(f"--{t.ljust(10)}---{QIAVisuals.c('OK', C_LIME)}--")
    
    qdo_content = f"#!/usr/bin/env bash\nQIA_INVOKED_AS=qdo python3 {self_path} \"$@\"\n"
    qdo_path = bin_dir / "qdo"
    qdo_path.write_text(qdo_content)
    qdo_path.chmod(0o755)
    print(f"--qdo{''.ljust(8)}---{QIAVisuals.c('OK', C_LIME)}--")
    
    print(QIAVisuals.c("\n--- INSTALACIÓN COMPLETADA ---", C_LIME))

def cmd_qia_status():
    for line in LOGO_LARGE:
        print(QIAVisuals.c(line, C_LIME))
    print(f"\nQIA Version: {VERSION}")
    print(f"Backend: {BACKEND_URL} [{'ACTIVO' if QIABackend.is_ready() else 'OFF'}]")
    print(f"Modelo: {QIAConfig.get_model()}")
    print(f"Perfil: {QIAConfig.get_profile()}")

def cmd_qia_help():
    for i, line in enumerate(LOGO_SMALL):
        prefix = f"{QIAVisuals.c(line, C_LIME)}   "
        if i == 1: print(f"{prefix}{QIAVisuals.c('QIA v' + VERSION, C_WHITE)} - IA para LARLAB")
        elif i == 2: print(f"{prefix}{QIAVisuals.c('Asistente técnico especializado.', C_GRAY)}")
        else: print(prefix)
    
    print(f"\n{QIAVisuals.c('MODOS DE USO:', C_LIME)}")
    print(f"  {QIAVisuals.c('q', C_YELLOW)} \"pregunta\"      Consultas rápidas (máx. 2 párrafos).")
    print(f"  {QIAVisuals.c('qdo', C_YELLOW)} \"pedido\"      Sintetizador Bash (menú interactivo).")
    print(f"  {QIAVisuals.c('qcode', C_YELLOW)} \"pedido\"    Generador de código (menú interactivo).")
    
    print(f"\n{QIAVisuals.c('SUBCOMANDOS QIA:', C_LIME)}")
    print(f"  {QIAVisuals.c('qia status', C_YELLOW)}        Estado del backend, modelo y perfil.")
    print(f"  {QIAVisuals.c('qia stop', C_YELLOW)}          Detiene el servidor (llama-server).")
    print(f"  {QIAVisuals.c('qia install', C_YELLOW)}       Configura accesos en ~/bin.")
    print(f"  {QIAVisuals.c('qia help', C_YELLOW)}          Muestra este manual.")
    
    print(f"\n{QIAVisuals.c('CONFIGURACIÓN RÁPIDA:', C_LIME)}")
    print(f"  {QIAVisuals.c('qmodel', C_YELLOW)} <archivo>    Cambia el modelo GGUF.")
    print(f"  {QIAVisuals.c('qprofile', C_YELLOW)} <nombre>   Cambia el perfil activo.")
    print()

def cmd_qia_model(args):
    model_dir = Path.home() / "local-llm" / "models" / "qwen2.5-coder-3b"
    if not args:
        print(QIAVisuals.c("\nModelos disponibles:", C_LIME))
        current = QIAConfig.get_model()
        if model_dir.exists():
            for f in model_dir.glob("*.gguf"):
                star = "*" if f.name == current else " "
                print(f" {QIAVisuals.c(star, C_YELLOW)} {f.name}")
        print(f"\nUso: qmodel <nombre_archivo>")
        return

    new_model = args[0]
    if (model_dir / new_model).exists():
        QIAConfig.set_model(new_model)
        print(QIAVisuals.c(f"✔ Modelo cambiado a: {new_model}", C_LIME))
        print(QIAVisuals.c("Nota: Reinicia con 'qia stop' para aplicar en la próxima consulta.", C_GRAY))
    else:
        print(QIAVisuals.c(f"Error: El modelo {new_model} no existe en la carpeta de modelos.", C_RED))

def cmd_qia_profile(args):
    if not args:
        print(QIAVisuals.c("\nPerfiles disponibles:", C_LIME))
        current = QIAConfig.get_profile()
        for p in PROFILES:
            star = "*" if p == current else " "
            print(f" {QIAVisuals.c(star, C_YELLOW)} {p.ljust(10)} {QIAVisuals.c(PROFILES[p], C_GRAY)}")
        print(f"\nUso: qprofile <nombre>")
        return

    new_profile = args[0]
    if new_profile in PROFILES:
        PROFILE_FILE.write_text(new_profile + "\n")
        print(QIAVisuals.c(f"✔ Perfil cambiado a: {new_profile}", C_LIME))
    else:
        print(QIAVisuals.c(f"Error: Perfil '{new_profile}' no reconocido.", C_RED))

def handle_qdo(prompt):
    while True:
        answer, elapsed = query_llm(prompt, mode="qdo")
        
        # Extracción robusta del comando
        # 1. Intentar sacar contenido de bloques markdown si el modelo ignoró la instrucción
        blocks = re.findall(r"```(?:bash|sh)?\n?(.*?)```", answer, re.DOTALL)
        if blocks:
            clean_cmd = blocks[0].strip()
        else:
            # 2. Si no hay bloques, limpiar texto conversacional típico
            lines = answer.split("\n")
            # Filtrar líneas que parecen explicaciones (empiezan con mayúscula y terminan en punto, o son muy largas)
            cmd_lines = []
            for line in lines:
                l = line.strip()
                if not l: continue
                # Si la línea empieza con un prompt común, lo quitamos
                l = re.sub(r"^[\$#>\s]+", "", l)
                # Si parece un comando (no termina en punto y no empieza con verbos explicativos)
                if not (re.match(r"^[A-Z][a-z]+", l) and l.endswith(".")):
                    cmd_lines.append(l)
            
            clean_cmd = "\n".join(cmd_lines).strip()
            # Si después de filtrar no queda nada, volvemos al original por si acaso
            if not clean_cmd: clean_cmd = answer.strip()

        # Limpieza final de caracteres extra
        clean_cmd = clean_cmd.replace("`", "").strip()
        
        if not clean_cmd:
            print(QIAVisuals.c("\nError: El modelo no generó un comando válido.", C_RED))
            break

        print(f"\n{QIAVisuals.c(f'# Tiempo: {elapsed:.2f}s', C_GRAY)}")
        
        while True:
            choice = input(f"\n{QIAVisuals.c('[E]', C_LIME)}jecutar / {QIAVisuals.c('[R]', C_YELLOW)}efinar / {QIAVisuals.c('[X]', C_BLUE)}plicar / {QIAVisuals.c('[C]', C_RED)}ancelar? ").lower()
            
            if choice == 'e':
                print(f"\n$ {clean_cmd}")
                subprocess.run(clean_cmd, shell=True)
                return
            elif choice == 'r':
                refinement = input("¿Qué quieres ajustar?: ")
                prompt = f"Comando anterior: {clean_cmd}\nAjuste pedido: {refinement}\nGenera el nuevo comando bash plano."
                break
            elif choice == 'x':
                print(f"\n{QIAVisuals.c('Explicación:', C_BLUE)}")
                query_llm(f"Explica brevemente qué hace este comando bash:\n{clean_cmd}", mode="q")
                print()
            else:
                print(QIAVisuals.c("Cancelado.", C_RED))
                return

def handle_qcode(prompt):
    while True:
        answer, elapsed = query_llm(prompt, mode="qcode")
        
        # Extracción robusta de código
        blocks = re.findall(r"```[a-zA-Z]*\n?(.*?)```", answer, re.DOTALL)
        clean_code = blocks[0].strip() if blocks else answer.strip()
        
        if not clean_code:
            print(QIAVisuals.c("\nError: No se generó código.", C_RED))
            break

        print(f"\n{QIAVisuals.c(f'# Tiempo: {elapsed:.2f}s', C_GRAY)}")
        
        while True:
            choice = input(f"\n{QIAVisuals.c('[G]', C_LIME)}uardar / {QIAVisuals.c('[R]', C_YELLOW)}efinar / {QIAVisuals.c('[X]', C_BLUE)}plicar / {QIAVisuals.c('[C]', C_RED)}ancelar? ").lower()
            
            if choice == 'g':
                # Intentar detectar extensión sin imprimirla directamente
                ext_prompt = f"Basado en este código, responde SOLO la extensión de archivo adecuada (ej: .py, .js, .sh):\n{clean_code[:200]}"
                # Usamos una versión silenciosa o extraemos el valor sin que query_llm ensucie la pantalla si es posible
                # En este script, query_llm imprime el label. Para la extensión, queremos algo discreto.
                
                # Para evitar que query_llm imprima "Comando Propuesto" etc, usamos modo "q" que es genérico
                ext, _ = query_llm(ext_prompt, mode="q")
                ext = ext.strip().lower()
                if not ext.startswith("."): ext = "." + ext
                
                print(f"\n{QIAVisuals.c('Guardar archivo:', C_LIME)}")
                path_input = input(f"Nombre o ruta del archivo (sugerido: código{ext}): ") or f"codigo{ext}"
                
                full_path = Path(path_input).expanduser().resolve()
                
                try:
                    # Crear directorios si no existen
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(clean_code)
                    print(QIAVisuals.c(f"\n✔ Archivo guardado con éxito en:", C_LIME))
                    print(QIAVisuals.c(f"  {full_path}", C_WHITE))
                except Exception as e:
                    print(QIAVisuals.c(f"Error al guardar: {e}", C_RED))
                return
                
            elif choice == 'r':
                refinement = input("¿Qué quieres ajustar del código?: ")
                prompt = f"Código anterior:\n{clean_code}\nAjuste pedido: {refinement}\nGenera el nuevo código fuente completo."
                break
                
            elif choice == 'x':
                print(f"\n{QIAVisuals.c('Modo Explicación:', C_BLUE)}")
                print("El código puede ser largo. ¿Qué parte te gustaría entender mejor? (ej: 'el bucle', 'la función X', 'todo')")
                topic = input("> ")
                explain_prompt = f"Sobre este código:\n{clean_code}\n\nExplica específicamente: {topic}"
                query_llm(explain_prompt, mode="q")
                print()
                
            else:
                print(QIAVisuals.c("Cancelado.", C_RED))
                return

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
        else: print(f"Subcomando '{sub}' no reconocido. Usa 'qia help'.")
        return

    if invoked == "qmodel":
        cmd_qia_model(args)
        return
    
    if invoked == "qprofile":
        cmd_qia_profile(args)
        return

    if not args:
        if invoked in ("q", "qdo", "qcode"):
            print(f"Uso: {invoked} \"tu pedido o pregunta\"")
        else:
            cmd_qia_help()
        return

    prompt = " ".join(args)
    
    if invoked == "qdo":
        handle_qdo(prompt)
    elif invoked == "qcode":
        handle_qcode(prompt)
    else: # modo q
        answer, elapsed = query_llm(prompt, mode="q")
        print(f"\n\n{QIAVisuals.c(f'# Tiempo: {elapsed:.2f}s', C_GRAY)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Restaurar cursor y limpiar línea actual
        sys.stderr.write("\033[?25h\r\033[K")
        sys.stderr.flush()
        sys.exit(0)
