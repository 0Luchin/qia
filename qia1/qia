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

DEFAULT_MODEL = "qwen2.5-coder:3b"
DEFAULT_PROFILE = "terminal"

CONFIG_DIR = Path.home() / ".config" / "qia"
MODEL_FILE = CONFIG_DIR / "model"
PROFILE_FILE = CONFIG_DIR / "profile"
CUSTOM_PROFILE_FILE = CONFIG_DIR / "custom_profile.txt"
DESC_FILE = CONFIG_DIR / "descriptions.json"
COLOR_FILE = CONFIG_DIR / "color"

URL = "http://127.0.0.1:11434/api/generate"

C_RESET = "\033[0m"
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_CYAN = "\033[36m"
C_GRAY = "\033[90m"

def color_enabled():
    try:
        return COLOR_FILE.read_text(encoding="utf-8").strip() != "off"
    except Exception:
        return True

def set_color_state(state):
    ensure_config()
    COLOR_FILE.write_text(state + "\n", encoding="utf-8")

def c(text, color_code):
    if not color_enabled():
        return str(text)
    return f"{color_code}{text}{C_RESET}"



PROFILES = {
    "terminal": "Asistente técnico Linux/WSL, Bash, Python, redes e infra. Respuestas cortas, copiables y seguras.",
    "noc": "Asistente NOC. Diagnóstico seguro de red, servicios, puertos, DNS, SSH, logs y recursos. Priorizar inspección.",
    "bash": "Especialista Bash/Linux. Comandos simples, pipelines claros, grep awk sed find ss journalctl systemctl.",
    "python": "Experto Python para scripting e infra. Código simple, estándar, CLI, pathlib, argparse, subprocess, json, logging.",
    "reviewer": "Revisor conservador. Detectar errores, riesgos y mejoras mínimas. No reescribir de más.",
    "teacher": "Docente técnico breve. Explicar Linux, redes, Bash y Python con ejemplos mínimos.",
}

DEFAULT_DESCRIPTIONS = {
    "qwen2.5-coder:1.5b": "muy liviano / código simple / Bash básico / más rápido que 3B",
    "qwen2.5-coder:3b": "uso diario / código liviano / Bash / Python / scripts cortos",
    "qwen2.5-coder:7b": "mejor calidad para código / más lento / usar con paciencia",
    "deepseek-coder:1.3b": "muy liviano / pruebas rápidas / código simple",
    "deepseek-coder:6.7b": "código más fuerte / más pesado / scripts y debugging",
    "llama3.2:1b": "chat ultra liviano / respuestas rápidas / baja calidad técnica",
    "llama3.2:3b": "chat general / explicación / resumen / no ideal para código puro",
    "gemma3:1b": "general muy liviano / estudio básico / respuestas cortas",
    "gemma3:4b": "modelo general compacto / texto / estudio / explicación",
    "starcoder2:3b": "código liviano / alternativa coder / probar contra Qwen 3B",
    "starcoder2:7b": "código más pesado / alternativa coder / puede ser lento",
}

CATALOG = [
    ("qwen2.5-coder:1.5b", "muy compatible", "coder"),
    ("qwen2.5-coder:3b", "muy compatible", "coder"),
    ("qwen2.5-coder:7b", "compatible lento", "coder"),
    ("deepseek-coder:1.3b", "muy compatible", "coder"),
    ("deepseek-coder:6.7b", "compatible lento", "coder"),
    ("llama3.2:1b", "muy compatible", "general"),
    ("llama3.2:3b", "muy compatible", "general"),
    ("gemma3:1b", "muy compatible", "general"),
    ("gemma3:4b", "compatible", "general"),
    ("starcoder2:3b", "compatible", "coder"),
    ("starcoder2:7b", "compatible lento", "coder"),
]

GLOBAL_RULES = """
No inventes.
No uses Markdown ni backticks.
No uses Docker salvo pedido explícito.
No agregues saludos ni cierre.
Si falta información, decí qué falta.
Preferí comandos seguros de inspección.
"""

MODE_Q_RULES = """
Modo q:
Si pido comando, devolvé solo comando plano.
Si pido archivo, devolvé solo heredoc ejecutable.
Si pido explicación, respondé breve.
"""

MODE_QDO_RULES = """
Modo qdo:
Devolvé solo comando Bash ejecutable.
Puede ser una línea larga, pipeline o varias líneas si hace falta.
No expliques.
No uses Markdown.
No uses backticks.
No uses bloques de código.
No uses sudo salvo pedido explícito.
No uses comandos destructivos.
No uses curl|sh, wget|sh, eval, sh -c ni bash -c.
Si el pedido es amplio o riesgoso, devolvé un comando seguro de inspección.
"""

BLOCKED_QDO = [
    "rm -rf",
    "mkfs",
    "dd if=",
    "shutdown",
    "reboot",
    "poweroff",
    "halt",
    "chmod -r 777",
    "chmod -R 777",
    "chown -r",
    "chown -R",
    ":(){",
    ">/dev/sd",
    "sudo rm",
    "sudo tee /etc/",
    "systemctl restart",
    "systemctl stop",
    "killall",
    "pkill",
    "eval ",
    "| sh",
    "| bash",
    "| python",
    "| perl",
    "curl ",
    "wget ",
]

def ensure_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not MODEL_FILE.exists():
        MODEL_FILE.write_text(DEFAULT_MODEL + "\n", encoding="utf-8")

    if not PROFILE_FILE.exists():
        PROFILE_FILE.write_text(DEFAULT_PROFILE + "\n", encoding="utf-8")

    if not CUSTOM_PROFILE_FILE.exists():
        CUSTOM_PROFILE_FILE.write_text(PROFILES[DEFAULT_PROFILE] + "\n", encoding="utf-8")

    if not DESC_FILE.exists():
        DESC_FILE.write_text(json.dumps(DEFAULT_DESCRIPTIONS, indent=2, ensure_ascii=False), encoding="utf-8")

    if not COLOR_FILE.exists():
        COLOR_FILE.write_text("on\n", encoding="utf-8")

def read_text(path, fallback=""):
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return fallback

def get_model():
    ensure_config()
    return read_text(MODEL_FILE, DEFAULT_MODEL) or DEFAULT_MODEL


def stop_model(model):
    model = model.strip()

    if not model:
        return

    try:
        subprocess.run(
            ["ollama", "stop", model],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        pass

def set_model(model):
    ensure_config()
    new_model = model.strip()
    old_model = get_model()

    if old_model and old_model != new_model:
        stop_model(old_model)

    MODEL_FILE.write_text(new_model + "\\n", encoding="utf-8")

def get_profile_name():
    ensure_config()
    return read_text(PROFILE_FILE, DEFAULT_PROFILE) or DEFAULT_PROFILE

def get_profile_text():
    ensure_config()
    name = get_profile_name()

    if name == "custom":
        return read_text(CUSTOM_PROFILE_FILE, PROFILES[DEFAULT_PROFILE])

    return PROFILES.get(name, PROFILES[DEFAULT_PROFILE])

def set_profile(name):
    ensure_config()

    if name not in PROFILES and name != "custom":
        print(f"Perfil desconocido: {name}")
        print("Usá: qprofile list")
        sys.exit(1)

    PROFILE_FILE.write_text(name + "\n", encoding="utf-8")

def set_custom_profile(text):
    ensure_config()
    CUSTOM_PROFILE_FILE.write_text(text.strip() + "\n", encoding="utf-8")
    set_profile("custom")

def build_system(mode):
    profile = get_profile_text()

    if mode == "qdo":
        mode_rules = MODE_QDO_RULES
    else:
        mode_rules = MODE_Q_RULES

    return "\n\n".join([
        GLOBAL_RULES.strip(),
        profile.strip(),
        mode_rules.strip(),
    ])

def get_descriptions():
    ensure_config()

    try:
        data = json.loads(DESC_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    merged = dict(DEFAULT_DESCRIPTIONS)
    merged.update(data)
    return merged

def set_description(model, desc):
    ensure_config()
    data = get_descriptions()
    data[model] = desc
    DESC_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def model_desc(model):
    return get_descriptions().get(model, "sin descripción configurada")

def clean_answer(text):
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    text = text.strip()

    if text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()

    lines = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            continue
        lines.append(line)

    text = "\n".join(lines).strip()

    if text.lower().startswith("bash\n"):
        text = text[5:].strip()

    return text

def extract_command_for_qdo(text):
    text = clean_answer(text)
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]

    bad_starts = (
        "para ",
        "puedes ",
        "podés ",
        "este ",
        "esto ",
        "el comando",
        "comando",
        "si ",
        "nota",
        "explicación",
    )

    cleaned = []
    for line in lines:
        low = line.strip().lower()

        if low.startswith(bad_starts):
            continue

        if line.strip().endswith(":"):
            continue

        cleaned.append(line)

    if cleaned:
        return "\n".join(cleaned).strip()

    return text.strip()





def start_wait_counter(label):
    stop_event = threading.Event()

    logo_lines = [
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

    lime = "\033[38;5;118m"
    orange = "\033[38;5;215m"
    white = "\033[97m"
    gray = "\033[38;5;250m"
    reset = "\033[0m"

    thinking_colors = [orange, lime, white]

    hide_cursor = "\033[?25l"
    show_cursor = "\033[?25h"
    clear_line = "\033[2K"
    clear_down = "\033[J"

    word = "PENSANDO"
    positions = list(range(len(word))) + list(range(len(word) - 2, 0, -1))
    block_lines = len(logo_lines) + 2

    def thinking_word(pos):
        return "".join(ch.lower() if i == pos else ch for i, ch in enumerate(word))

    def logo_line_with_sparkles(line):
        # Base verde lima, tintineos puntuales naranja claro.
        chars = []
        for ch in line:
            if ch == "@" and random.random() < 0.10:
                chars.append(orange + "@" + lime)
            else:
                chars.append(ch)
        return lime + "".join(chars) + reset

    def draw(frame, elapsed):
        pos = positions[frame % len(positions)]
        word_color = thinking_colors[frame % len(thinking_colors)]

        current_second = int(elapsed)

        # Segundero:
        # - al cambiar cada segundo: blanco
        # - luego fade hacia verde/naranja
        # - con el paso del tiempo, el color base migra de verde a naranja
        second_phase = elapsed - current_second

        green_to_orange = [
            "[38;5;118m",  # verde lima
            "[38;5;154m",
            "[38;5;190m",
            "[38;5;226m",  # amarillo
            "[38;5;221m",
            "[38;5;215m",  # naranja claro
        ]

        # A los 10 segundos ya queda en naranja completo.
        base_idx = min(int((elapsed / 10.0) * (len(green_to_orange) - 1)), len(green_to_orange) - 1)
        base_color = green_to_orange[base_idx]

        # Pulso blanco al inicio de cada segundo; después cae al color base.
        if second_phase < 0.12:
            time_color = "[97m"
        elif second_phase < 0.25:
            time_color = "[38;5;255m"
        elif second_phase < 0.40:
            time_color = "[38;5;253m"
        else:
            time_color = base_color

        out = []

        for line in logo_lines:
            out.append(clear_line + logo_line_with_sparkles(line))

        status = (
            f"{word_color}[{thinking_word(pos)}]{reset} "
            f"- "
            f"{time_color}{elapsed:04.1f}s{reset}"
        )

        out.append(clear_line)
        out.append(clear_line + status)

        return "\n".join(out) + "\n"

    def run():
        start_time = time.perf_counter()
        frame = 0
        first_draw = True

        sys.stderr.write(hide_cursor)

        try:
            while not stop_event.is_set():
                elapsed = time.perf_counter() - start_time

                if not first_draw:
                    sys.stderr.write(f"\033[{block_lines}F")

                sys.stderr.write(draw(frame, elapsed))
                sys.stderr.flush()

                first_draw = False
                frame += 1

                # ~10 FPS con variación leve para no gastar CPU.
                if random.random() < 0.10:
                    delay = random.uniform(0.060, 0.080)
                elif random.random() < 0.12:
                    delay = random.uniform(0.140, 0.200)
                else:
                    delay = random.uniform(0.090, 0.120)

                time.sleep(delay)

        finally:
            elapsed = time.perf_counter() - start_time

            if not first_draw:
                sys.stderr.write(f"\033[{block_lines}F")
                sys.stderr.write(clear_down)

            sys.stderr.write(show_cursor)
            sys.stderr.write(f"[PENSANDO] listo en {elapsed:.2f}s\n")
            sys.stderr.flush()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return stop_event, thread


def llama_server_ready():
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8080/v1/models",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=1.5) as response:
            return response.status == 200
    except Exception:
        return False


def start_llama_server():
    model_path = os.path.expanduser(
        "~/local-llm/models/qwen2.5-coder-3b/qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    )
    server_bin = os.path.expanduser(
        "~/local-llm/llama.cpp/build/bin/llama-server"
    )

    if not os.path.exists(server_bin):
        print(c("Error: no encontré llama-server.", C_RED))
        print(server_bin)
        sys.exit(1)

    if not os.path.exists(model_path):
        print(c("Error: no encontré el modelo GGUF.", C_RED))
        print(model_path)
        sys.exit(1)

    log_dir = os.path.expanduser("~/.local/share/qia/logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "llama-server.log")

    log = open(log_path, "a", encoding="utf-8")

    subprocess.Popen(
        [
            server_bin,
            "-m", model_path,
            "-c", "2048",
            "-t", str(os.cpu_count() or 4),
            "--host", "127.0.0.1",
            "--port", "8080"
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )


def ensure_llama_server():
    if llama_server_ready():
        return

    print(c("# llama-server no está activo. Iniciando...", C_YELLOW), file=sys.stderr)
    start = time.perf_counter()
    start_llama_server()

    while time.perf_counter() - start < 120:
        if llama_server_ready():
            elapsed = time.perf_counter() - start
            print(c(f"# llama-server listo en {elapsed:.2f}s", C_GREEN), file=sys.stderr)
            return
        time.sleep(0.5)

    print(c("Error: llama-server no respondió después de 120s.", C_RED))
    print("Revisá el log:")
    print("~/.local/share/qia/logs/llama-server.log")
    sys.exit(1)




def wants_command_only(prompt):
    p = prompt.lower()
    triggers = (
        "solo comando",
        "solo comandos",
        "sin explicacion",
        "sin explicación",
        "comando plano",
        "comandos planos",
        "solo el comando",
        "solo los comandos",
    )
    return any(t in p for t in triggers)



def normalize_qdo_command(cmd):
    lines = [line.strip() for line in cmd.splitlines() if line.strip()]

    watch_lines = [line for line in lines if line.startswith("watch ")]
    if len(watch_lines) > 1:
        useful = []
        for line in watch_lines:
            m = re.search(r"['\"](.+?)['\"]", line)
            if m:
                useful.append(m.group(1).strip())

        if useful:
            joined = "; echo; ".join(useful[:5])
            return f"watch -n 1 'bash -c \"{joined}\"'"

    return cmd.strip()


def clean_command_only_answer(answer):
    cleaned = []

    for raw in answer.splitlines():
        line = raw.strip()

        if not line:
            continue

        # Extraer comando si vino entre backticks
        m = re.search(r"`([^`]+)`", line)
        if m:
            line = m.group(1).strip()

        # Sacar numeración o bullets
        line = re.sub(r"^\s*\d+[\.\)]\s*", "", line)
        line = re.sub(r"^\s*[-*]\s*", "", line)

        # Cortar descripciones típicas: comando - descripción
        if " - " in line:
            line = line.split(" - ", 1)[0].strip()

        # Evitar frases humanas
        low = line.lower()
        if low.startswith(("claro", "aquí", "aca", "estos", "puedes", "podés", "para ")):
            continue

        if line:
            cleaned.append(line)

    return "\n".join(cleaned).strip()


def harden_system_prompt(system, mode):
    base = system.strip()

    if mode == "qdo":
        extra = """
Reglas finales obligatorias:
- Devolvé SOLO comandos Bash ejecutables.
- No uses Markdown.
- No uses backticks.
- No expliques.
- Podés devolver varias líneas si hace falta.
- No uses comandos destructivos.
- Si el pedido es monitoreo o diagnóstico, preferí comandos robustos como ps, free, uptime, df, ss, journalctl, dmesg, ip, ping, curl.
- Si el usuario pide monitoreo "en vivo", "tiempo real", "actualizando" o similar, devolvé UN SOLO comando watch que agrupe todo con bash -c.
- No devuelvas varios watch separados.
- No devuelvas más de 5 líneas de comandos salvo que el usuario lo pida explícitamente.
- Si el comando necesita sudo, no lo ejecutes automáticamente salvo que el usuario lo pida.
- Evitá texto humano fuera del comando.
"""
    else:
        extra = """
Reglas finales obligatorias:
- Respuesta técnica corta.
- Máximo 8 líneas salvo que el usuario pida detalle.
- Si el usuario pide comandos, devolvé comandos planos.
- No uses Markdown ni backticks salvo que el usuario pida formato.
- No des introducciones tipo "Claro" o "Aquí tienes".
- Priorizá Linux, WSL, Bash, Python, redes e infraestructura.
"""

    return base + "\n\n" + extra.strip()


def ask_ollama(prompt, mode):
    ensure_llama_server()

    model = "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    system = harden_system_prompt(build_system(mode), mode)

    command_only = wants_command_only(prompt)
    if command_only:
        system += """
Regla extra para este pedido:
- El usuario pidió solo comando(s).
- Cada línea debe contener únicamente un comando ejecutable.
- No numeres.
- No agregues descripciones.
- No uses Markdown.
- No uses backticks.
"""

    start_time = time.perf_counter()
    wait_counter, wait_thread = start_wait_counter(f"llama.cpp {model}")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": prompt.strip()
            }
        ],
        "max_tokens": 140 if mode == "qdo" else 160,
        "temperature": 0.1,
        "top_p": 0.8,
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8080/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            answer = clean_answer(answer)
            if command_only:
                answer = clean_command_only_answer(answer)
            if mode == "qdo":
                answer = normalize_qdo_command(answer)
            elapsed = time.perf_counter() - start_time
            return answer, elapsed

    except TimeoutError:
        print("", file=sys.stderr)
        print(c("Error: timeout esperando respuesta de llama-server.", C_RED))
        print("Probá con un pedido más específico o reiniciá el backend:")
        print("pkill -f llama-server")
        sys.exit(1)

    except urllib.error.URLError:
        print("", file=sys.stderr)
        print(c("Error: llama-server no responde en http://127.0.0.1:8080", C_RED))
        print("Probá revisar:")
        print("~/.local/share/qia/logs/llama-server.log")
        sys.exit(1)

    finally:
        wait_counter.set()
        wait_thread.join(timeout=1.0)


def safe_clipboard_text(text):
    text = text.strip()

    if not text:
        return None

    low = text.lower()

    narrative_starts = (
        "para ",
        "puedes ",
        "podés ",
        "este comando",
        "el comando",
        "aquí ",
        "nota:",
        "si ",
        "esto ",
    )

    if low.startswith(narrative_starts):
        return None

    # Heredoc: es copiable
    if "cat >" in text and "<<'EOF'" in text:
        return text

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return None

    # Si hay muchas líneas y no es heredoc, no copiar automáticamente
    if len(lines) > 3:
        return None

    command_starts = (
        "ping ", "curl ", "wget ", "ss ", "netstat ", "ip ", "dig ", "nslookup ",
        "journalctl ", "systemctl ", "ps ", "top ", "htop ", "free ", "df ", "du ",
        "grep ", "awk ", "sed ", "find ", "cat ", "tail ", "head ", "ls ", "tree ",
        "python ", "python3 ", "bash ", "chmod ", "mkdir ", "touch ", "tar ",
        "echo ", "uname ", "lscpu ", "free", "watch "
    )

    first = lines[0].lower()

    if first.startswith(command_starts):
        return text

    # Pipelines o comandos compuestos
    if "|" in text or "&&" in text or ";" in text:
        return text

    return None


def copy_to_clipboard(text):
    try:
        subprocess.run(
            ["clip.exe"],
            input=text.encode("utf-16le"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except Exception:
        return False

def is_blocked_qdo(cmd):
    low = cmd.lower()
    return any(pattern.lower() in low for pattern in BLOCKED_QDO)

def get_installed_models_full():
    try:
        result = subprocess.run(["ollama", "list"], text=True, capture_output=True, check=False)
    except FileNotFoundError:
        print("Error: no encuentro el comando ollama.")
        return []

    lines = result.stdout.strip().splitlines()
    rows = []

    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 3:
            rows.append({
                "name": parts[0],
                "id": parts[1],
                "size": parts[2],
                "modified": " ".join(parts[3:]) if len(parts) > 3 else ""
            })

    return rows

def get_installed_models():
    return [row["name"] for row in get_installed_models_full()]

def qmodel_list():
    rows = get_installed_models_full()
    current = get_model()

    if not rows:
        print("No encontré modelos instalados.")
        return

    print("Modelos instalados:\n")

    for row in rows:
        name = row["name"]
        current_mark = " [actual]" if name == current else ""
        print(f"- {name}{current_mark}")
        print(f"  tamaño: {row['size']}")
        print(f"  uso: {model_desc(name)}")
        print()

def qmodel_catalog():
    installed = set(get_installed_models())
    current = get_model()

    print("Catálogo sugerido para esta PC:\n")

    for model, fit, typ in CATALOG:
        status = "instalado" if model in installed else "no instalado"
        current_mark = " [actual]" if model == current else ""
        print(f"- {model}{current_mark}")
        print(f"  estado: {status}")
        print(f"  compatibilidad: {fit}")
        print(f"  tipo: {typ}")
        print(f"  uso: {model_desc(model)}")
        print(f"  pull: ollama pull {model}")
        print()

def qmodel_pulls():
    installed = set(get_installed_models())

    print("Comandos sugeridos para descargar modelos no instalados:\n")

    for model, fit, typ in CATALOG:
        if model not in installed:
            print(f"ollama pull {model}    # {model_desc(model)}")

def qmodel_select():
    rows = get_installed_models_full()

    if not rows:
        print("No encontré modelos instalados. Probá: ollama list")
        sys.exit(1)

    current = get_model()
    print("Seleccioná modelo predeterminado:\n")

    for i, row in enumerate(rows, start=1):
        name = row["name"]
        marker = "  [actual]" if name == current else ""
        print(f"{i}) {name}{marker}")
        print(f"   tamaño: {row['size']}")
        print(f"   uso: {model_desc(name)}")
        print()

    choice = input("Elegí número, o Enter para cancelar: ").strip()

    if not choice:
        print(c("Cancelado.", C_YELLOW))
        return

    if not choice.isdigit():
        print("Selección inválida.")
        sys.exit(1)

    index = int(choice) - 1

    if index < 0 or index >= len(rows):
        print("Selección fuera de rango.")
        sys.exit(1)

    chosen = rows[index]["name"]
    set_model(chosen)
    print(f"Modelo predeterminado: {chosen}")

def qmodel_descs():
    descs = get_descriptions()

    print("Descripciones configuradas:\n")
    for model in sorted(descs):
        print(f"- {model}: {descs[model]}")

def qprofile_select():
    current = get_profile_name()
    names = list(PROFILES.keys()) + ["custom"]

    print("Seleccioná perfil:\n")

    descs = {
        "terminal": "copiloto general de terminal",
        "noc": "diagnóstico NOC / redes / servicios / logs",
        "bash": "Bash, pipelines y comandos Linux",
        "python": "Python para scripting e infraestructura",
        "reviewer": "revisión conservadora de código/comandos",
        "teacher": "explicación técnica breve",
        "custom": "perfil personalizado editable",
    }

    for i, name in enumerate(names, start=1):
        marker = "  [actual]" if name == current else ""
        print(f"{i}) {name}{marker}")
        print(f"   uso: {descs.get(name, '')}")
        print()

    choice = input("Elegí número, o Enter para cancelar: ").strip()

    if not choice:
        print(c("Cancelado.", C_YELLOW))
        return

    if not choice.isdigit():
        print("Selección inválida.")
        sys.exit(1)

    index = int(choice) - 1

    if index < 0 or index >= len(names):
        print("Selección fuera de rango.")
        sys.exit(1)

    chosen = names[index]

    if chosen == "custom":
        print()
        print("Pegá o escribí tu perfil custom.")
        print("Para terminar, ingresá una línea que diga solo: EOF")
        print()

        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break

            if line.strip() == "EOF":
                break

            lines.append(line)

        custom_text = "\n".join(lines).strip()

        if not custom_text:
            print("Custom vacío. Cancelado.")
            return

        set_custom_profile(custom_text)
        print("Perfil actual: custom")
        return

    set_profile(chosen)
    print(f"Perfil actual: {chosen}")

def qprofile_list():
    current = get_profile_name()

    print("Perfiles disponibles:\n")
    for name in PROFILES:
        marker = " [actual]" if name == current else ""
        print(f"- {name}{marker}")

    custom_marker = " [actual]" if current == "custom" else ""
    print(f"- custom{custom_marker}")

def qprofile_show():
    current = get_profile_name()
    print(f"Perfil actual: {current}\n")
    print(get_profile_text())

def qprofile_path():
    ensure_config()
    print(f"Config dir: {CONFIG_DIR}")
    print(f"Modelo:     {MODEL_FILE}")
    print(f"Perfil:     {PROFILE_FILE}")
    print(f"Custom:     {CUSTOM_PROFILE_FILE}")
    print(f"Descs:      {DESC_FILE}")

def qprofile_edit():
    ensure_config()
    editor = os.environ.get("EDITOR", "nano")

    if get_profile_name() != "custom":
        CUSTOM_PROFILE_FILE.write_text(get_profile_text().strip() + "\n", encoding="utf-8")
        set_profile("custom")

    subprocess.run([editor, str(CUSTOM_PROFILE_FILE)])
    print("Perfil actual: custom")


def handle_qcolor(args):
    ensure_config()

    if not args:
        state = "on" if color_enabled() else "off"
        print(f"color: {state}")
        return

    cmd = args[0].lower()

    if cmd == "on":
        set_color_state("on")
        print(c("Color activado.", C_GREEN))
        return

    if cmd == "off":
        set_color_state("off")
        print("Color desactivado.")
        return

    if cmd == "toggle":
        if color_enabled():
            set_color_state("off")
            print("Color desactivado.")
        else:
            set_color_state("on")
            print(c("Color activado.", C_GREEN))
        return

    print("Uso: qcolor [on|off|toggle]")
    sys.exit(1)


def usage():
    print("""Uso:
  q "pedido"                       Genera respuesta/comando y copia al portapapeles
  qdo "pedido"                     Genera comando/pipeline, pide confirmación y ejecuta

  qmodel                           Muestra modelo actual
  qmodel show                      Muestra modelo actual
  qmodel list                      Lista modelos instalados con descripción
  qmodel select                    Elegir modelo instalado por número
  qmodel reset                     Vuelve a qwen2.5-coder:3b
  qmodel catalog                   Lista modelos sugeridos aunque no estén instalados
  qmodel pulls                     Muestra comandos pull sugeridos
  qmodel desc MODELO "texto"       Agrega o cambia descripción
  qmodel descs                     Lista descripciones configuradas

  qprofile                         Muestra perfil actual
  qprofile show                    Muestra perfil actual completo
  qprofile list                    Lista perfiles
  qprofile select                  Elegir perfil por número
  qprofile custom "texto"          Setea perfil custom desde argumento
  qprofile edit                    Edita perfil custom con nano
  qprofile reset                   Vuelve a perfil terminal
  qprofile path                    Muestra archivos de configuración
""")

def handle_qmodel(args):
    if not args:
        print(get_model())
        return

    cmd = args[0]

    if cmd == "show":
        print(get_model())
        return

    if cmd == "list":
        qmodel_list()
        return

    if cmd == "catalog":
        qmodel_catalog()
        return

    if cmd == "pulls":
        qmodel_pulls()
        return

    if cmd == "select":
        qmodel_select()
        return

    if cmd == "reset":
        set_model(DEFAULT_MODEL)
        print(f"Modelo predeterminado: {DEFAULT_MODEL}")
        return

    if cmd == "desc":
        if len(args) < 3:
            print('Uso: qmodel desc MODELO "descripción"')
            sys.exit(1)
        model = args[1]
        desc = " ".join(args[2:])
        set_description(model, desc)
        print(f"Descripción guardada para {model}: {desc}")
        return

    if cmd == "descs":
        qmodel_descs()
        return

    usage()
    sys.exit(1)

def handle_qprofile(args):
    if not args:
        print(get_profile_name())
        return

    cmd = args[0]

    if cmd == "show":
        qprofile_show()
        return

    if cmd == "list":
        qprofile_list()
        return

    if cmd == "select":
        qprofile_select()
        return

    if cmd == "custom":
        if len(args) < 2:
            print('Uso: qprofile custom "texto del perfil"')
            sys.exit(1)
        text = " ".join(args[1:])
        set_custom_profile(text)
        print("Perfil actual: custom")
        return

    if cmd == "edit":
        qprofile_edit()
        return

    if cmd == "reset":
        set_profile(DEFAULT_PROFILE)
        print(f"Perfil actual: {DEFAULT_PROFILE}")
        return

    if cmd == "path":
        qprofile_path()
        return

    usage()
    sys.exit(1)



def qia_logo():
    lime = "\033[38;5;118m"
    orange = "\033[38;5;215m"
    reset = "\033[0m"

    logo = [
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

    for i, line in enumerate(logo):
        color = lime if i % 2 == 0 else orange
        print(color + line + reset)

    print()


def qia_status():
    qia_logo()
    print("qia status")
    print()

    if llama_server_ready():
        print("backend: llama-server activo")
        print("url: http://127.0.0.1:8080")
    else:
        print("backend: llama-server detenido")

    model_path = os.path.expanduser(
        "~/local-llm/models/qwen2.5-coder-3b/qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    )
    server_bin = os.path.expanduser(
        "~/local-llm/llama.cpp/build/bin/llama-server"
    )

    print(f"llama-server: {'OK' if os.path.exists(server_bin) else 'NO ENCONTRADO'}")
    print(f"modelo GGUF: {'OK' if os.path.exists(model_path) else 'NO ENCONTRADO'}")


def qia_stop():
    subprocess.run(
        ["pkill", "-f", "llama-server"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )
    print("llama-server detenido")


def qia_doctor():
    qia_logo()
    print("qia doctor")
    print()

    checks = [
        ("python", sys.executable),
        ("llama-server", os.path.expanduser("~/local-llm/llama.cpp/build/bin/llama-server")),
        ("modelo", os.path.expanduser("~/local-llm/models/qwen2.5-coder-3b/qwen2.5-coder-3b-instruct-q4_k_m.gguf")),
    ]

    ok = True

    for name, target in checks:
        exists = os.path.exists(target) if name != "python" else True
        print(f"{name}: {'OK' if exists else 'FALTA'} -> {target}")
        ok = ok and exists

    print()
    print(f"backend activo: {'SI' if llama_server_ready() else 'NO'}")

    if ok:
        print("estado general: OK")
    else:
        print("estado general: revisar faltantes")


def main():
    invoked = Path(sys.argv[0]).name

    if invoked in ("qia.py", "qia") and len(sys.argv) >= 2:
        cmd = sys.argv[1].strip().lower()

        if cmd == "status":
            qia_status()
            return

        if cmd == "stop":
            qia_stop()
            return

        if cmd == "doctor":
            qia_doctor()
            return

        if cmd in ("help", "-h", "--help"):
            print("Uso:")
            print("  q \"pregunta\"")
            print("  qdo \"pedido de comando\"")
            print("  qia status")
            print("  qia stop")
            print("  qia doctor")
            return

    invoked_as = os.path.basename(sys.argv[0])

    if invoked_as == "qmodel":
        handle_qmodel(sys.argv[1:])
        return

    if invoked_as == "qprofile":
        handle_qprofile(sys.argv[1:])
        return

    if invoked_as == "qcolor":
        handle_qcolor(sys.argv[1:])
        return

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    if invoked_as == "qdo":
        cmd, elapsed = ask_ollama(prompt, "qdo")
        cmd = extract_command_for_qdo(cmd)

        print("\n" + c("Comando propuesto:", C_BLUE) + "\n")
        print(c(cmd, C_CYAN))
        print(f"\n{c(f'# Tiempo: {elapsed:.2f}s', C_GRAY)}\n")

        if is_blocked_qdo(cmd):
            print(c("Bloqueado por seguridad.", C_RED))
            print("Usá q si querés generar el comando para revisarlo manualmente.")
            sys.exit(1)

        confirm = input("Ejecutar? [y/N]: ").strip().lower()

        if confirm == "y":
            try:
                subprocess.run(cmd, shell=True)
            except KeyboardInterrupt:
                print()
                print("Interrumpido por el usuario.")
        else:
            print(c("Cancelado.", C_YELLOW))

    else:
        answer, elapsed = ask_ollama(prompt, "q")
        print(c(answer, C_CYAN))
        print(f"\n{c(f'# Tiempo: {elapsed:.2f}s', C_GRAY)}")

        # Copiado automático desactivado.

if __name__ == "__main__":
    main()
