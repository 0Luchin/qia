#!/usr/bin/env bash
# scripts/install.sh - Instalador de QIA

set -e

# Configuración
LOG_FILE="install.log"
BIN_DIR="$HOME/bin"
LLAMA_DIR="$HOME/local-llm/llama.cpp"
MODEL_DIR="$HOME/local-llm/models/qwen2.5-coder-3b"
MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf"
PORT=18080
THRESHOLD_GB=5

# Utilidad de logging y spinner
log() { echo "[$(date +'%Y-%m-%dT%H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

run_with_spinner() {
    local msg="$1"
    shift
    echo -n "$msg... "
    ("$@") >> "$LOG_FILE" 2>&1 &
    local pid=$!
    local spinner="-\|/"
    while [ -d /proc/$pid ]; do
        for (( i=0; i<${#spinner}; i++ )); do
            echo -n "${spinner:$i:1}"
            sleep 0.2
            echo -n $'\b'
        done
    done
    wait $pid
    if [ $? -eq 0 ]; then
        echo "✅"
    else
        echo "❌ Falló. Revisa '$LOG_FILE'."
        exit 1
    fi
}

# --- Funciones ---

check_deps() {
    log "--- Verificando dependencias ---"
    for cmd in git cmake make g++ python3; do
        if ! command -v $cmd > /dev/null 2>&1; then
            echo "❌ Error: $cmd no está instalado. Ejecuta: sudo apt install $cmd"
            exit 1
        fi
    done
    log "✅ Todas las dependencias encontradas."
}

check_disk() {
    log "--- Verificando espacio en disco ---"
    AVAILABLE_GB=$(df -BG ~ | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$AVAILABLE_GB" -lt "$THRESHOLD_GB" ]; then
        echo "❌ Error: Espacio insuficiente. Necesitas al menos ${THRESHOLD_GB}GB libres."
        exit 1
    fi
    log "✅ Espacio en disco suficiente."
}

confirm() {
    if [[ "$NON_INTERACTIVE" == "1" ]]; then return 0; fi
    read -p "$1 (y/n): " choice
    case "$choice" in
        y|Y ) return 0;;
        * ) return 1;;
    esac
}

build_llama() {
    log "--- Preparando llama.cpp ---"
    mkdir -p "$HOME/local-llm"
    
    # Comprobar si ya está compilado
    if [ -d "$LLAMA_DIR" ] && [ -f "$LLAMA_DIR/build/bin/llama-server" ]; then
        log "✅ llama.cpp ya existe y parece estar compilado. Saltando compilación."
        return
    fi

    if [ ! -d "$LLAMA_DIR" ]; then
        if confirm "No se encontró llama.cpp. ¿Descargar e instalar en $LLAMA_DIR?"; then
            run_with_spinner "Clonando repositorio" git clone https://github.com/ggerganov/llama.cpp "$LLAMA_DIR"
        else
            echo "❌ Instalación abortada."
            exit 1
        fi
    fi
    
    run_with_spinner "Compilando motor" bash -c "cd '$LLAMA_DIR' && mkdir -p build && cd build && cmake .. && make -j$(nproc --ignore=1 2>/dev/null || echo 1)"
}

download_model() {
    log "--- Preparando modelo ---"
    mkdir -p "$MODEL_DIR"
    
    if [ -f "$MODEL_DIR/qwen2.5-coder-3b-instruct-q4_k_m.gguf" ]; then
        log "✅ Modelo ya existente. Saltando descarga."
        return
    fi

    if confirm "No se encontró el modelo. ¿Descargar (~2GB) en $MODEL_DIR?"; then
        run_with_spinner "Descargando modelo" wget --continue --tries=3 --timeout=30 -O "$MODEL_DIR/qwen2.5-coder-3b-instruct-q4_k_m.gguf" "$MODEL_URL"
    else
        echo "❌ Instalación abortada."
        exit 1
    fi
    log "✅ Modelo listo."
}

install_qia() {
    log "--- Instalando QIA ---"
    mkdir -p "$BIN_DIR"
    mkdir -p "$HOME/.config/qia"
    if [ ! -f "$HOME/.config/qia/port" ]; then echo "$PORT" > "$HOME/.config/qia/port"; fi
    
    cp qia.py "$BIN_DIR/qia.py"
    chmod +x "$BIN_DIR/qia.py"
    
    ln -sf "$BIN_DIR/qia.py" "$BIN_DIR/q"
    ln -sf "$BIN_DIR/qia.py" "$BIN_DIR/qcode"
    ln -sf "$BIN_DIR/qia.py" "$BIN_DIR/qia"
    
    echo '#!/usr/bin/env bash' > "$BIN_DIR/qdo"
    echo 'QIA_INVOKED_AS=qdo python3 '"$BIN_DIR/qia.py"' "$@"' >> "$BIN_DIR/qdo"
    chmod +x "$BIN_DIR/qdo"
    
    log "--- Verificando PATH ---"
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        if confirm "Añadir $BIN_DIR a ~/.bashrc?"; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
            log "✅ ~/.bashrc actualizado. Ejecuta 'source ~/.bashrc' para aplicar cambios."
        else
            echo "⚠️ AVISO: QIA no funcionará directamente. Añade $BIN_DIR a tu PATH manualmente."
        fi
    fi
    log "✅ QIA instalado correctamente."
}

# --- Ejecución ---
check_deps
check_disk
build_llama
download_model
install_qia
log "--- ¡Instalación exitosa! ---"
