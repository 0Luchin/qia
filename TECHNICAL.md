# QIA v2 - Quantum Infrastructure Assistant (Deep Dive)

QIA es un asistente de terminal modular diseñado para interactuar con modelos de lenguaje locales (LLMs) a través de un backend compatible con la API de OpenAI (por defecto `llama-server` en el puerto 8080).

## Arquitectura del Código (`qia.py`)

El script único `qia.py` actúa como orquestador y cliente, cambiando su comportamiento según cómo sea invocado (subcomandos).

### 1. Gestión de Configuración (`QIAConfig`)
- Centraliza la persistencia en `~/.config/qia/`.
- Maneja el modelo actual, el perfil del asistente, las preferencias de color y la **paleta de colores seleccionada**.
- Asegura que los directorios y archivos necesarios existan al iniciar.

### 2. Capa Visual (`QIAVisuals`)
- Proporciona colores ANSI dinámicos (basados en la paleta activa) y animaciones de carga.
- `animate_logo_big`: Animación principal con destello tri-color y mensajes de progreso.
- `animate_logo`: Animación pequeña (usada en `help`).
- `colored_text`: Generador de texto con colores aleatorios basados en la paleta actual.

### 3. Sistema de Paletas de Colores
- Definidas en el diccionario `PALETTES` (5 esquemas).
- `get_c(tipo)`: Función dinámica que recupera el color correcto según la paleta configurada en `COLOR_FILE`.
- Colores accesibles como funciones (`C_LIME()`, `C_ORANGE()`, `C_CYAN()`) para evitar dependencias circulares.

### 4. Backend Manager (`QIABackend`)
- Gestiona la ejecución de `llama-server`.
- **Puerto:** Por defecto `18080`.
- **Compilación:** `make install` compila `llama.cpp`.

### 5. Lógica de Comandos y Modos
- **Subcomandos (`qia <subcommand>`):**
    - `install`, `doctor`, `status`, `color`, `model`, `profile`, `update`, `stop`, `help`.
- **Modos de Invocación:**
    - `q`: Chat técnico directo.
    - `qdo`: Sintetizador de comandos Bash.
    - `qcode`: Generador de código puro.

---

## Guía para IAs (Contexto de Sistema)

Si eres una IA trabajando en este código:
- **Estructura:** El código es monolítico.
- **Colores:** NO uses constantes estáticas. Usa `C_LIME()`, `C_ORANGE()`, `C_CYAN()` (que llaman a `get_c()`).
- **Comandos:** Toda lógica nueva debe ser un subcomando de `qia` y registrarse en `main()`.
- **Seguridad:** `qdo` ejecuta comandos directamente; mantén la rigidez del `system_prompt`.

## Uso Rápido

- `qia help`: Menú de comandos actualizado.
- `qia color <1-5>`: Cambiar paleta.
- `qia update`: Actualiza QIA y reinstala.
- `q "pregunta"`: Chat rápido.
- `qdo "acción"`: Genera comando.
- `qcode "tarea"`: Genera código.
- `qia status`: Ver estado del backend.

