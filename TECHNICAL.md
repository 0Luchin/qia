# QIA v2 - Quantum Infrastructure Assistant (Deep Dive)

QIA es un asistente de terminal modular diseñado para interactuar con modelos de lenguaje locales (LLMs) a través de un backend compatible con la API de OpenAI (por defecto `llama-server` en el puerto 8080).

## Arquitectura del Código (`qia.py`)

El script único `qia.py` actúa como orquestador y cliente, cambiando su comportamiento según cómo sea invocado (vía enlaces simbólicos).

### 1. Gestión de Configuración (`QIAConfig`)
- Centraliza la persistencia en `~/.config/qia/`.
- Maneja el modelo actual, el perfil del asistente y las preferencias de color.
- Asegura que los directorios y archivos necesarios existan al iniciar.

### 2. Capa Visual (`QIAVisuals`)
- Proporciona colores ANSI y animaciones de carga.
- `animate_logo`: Muestra un logo ASCII animado en `stderr` mientras el LLM procesa, permitiendo ver el tiempo transcurrido sin interferir con la salida estándar (`stdout`).

### 3. Backend Manager (`QIABackend`)
- Gestiona la ejecución de `llama-server`.
- `ensure()`: Verifica si el servidor está activo; si no, lo inicia automáticamente usando el binario y modelo configurados en las rutas estándar de LARLAB.

### 4. Lógica de Prompting y Modos
- **Perfiles:** Define la "personalidad" (terminal, noc, python).
- **Modos de Invocación:**
    - `q`: Chat técnico directo. Respuestas breves.
    - `qdo`: Sintetizador de comandos. El sistema es extremadamente estricto para devolver solo Bash ejecutable. Incluye lógica de "Few-Shot" en el prompt para guiar al modelo.
    - `qcode`: Generador de código puro. Ahora interactivo (Guardar/Refinar/Explicar).

### 5. Flujo de Ejecución en `qdo` y `qcode`
Este es el componente más crítico para la automatización:
1. **Consulta:** Pide el comando o código al LLM.
2. **Extracción:** Si el LLM incluye explicaciones o bloques Markdown (```), el script utiliza expresiones regulares para extraer **solo** el código fuente o el comando.
3. **Limpieza (en qdo):** Filtra líneas que parecen explicaciones humanas y elimina prompts accidentales (`$`, `>`).
4. **Interactividad:**
    - `qdo`: `[E]jecutar`, `[R]efinar`, `[X]plicar`, `[C]ancelar`.
    - `qcode`: `[G]uardar` (con detección automática de extensión), `[R]efinar`, `[X]plicar` (selectivo), `[C]ancelar`.

### 6. Sistema de Detección de Archivos (en `qcode`)
Cuando eliges `[G]uardar`, `qcode` realiza una mini-consulta interna al modelo para predecir la extensión correcta (`.py`, `.js`, `.c`, etc.) basándose en el contenido generado, facilitando la organización del trabajo.

### 7. Modo Explicación Selectiva
Para evitar respuestas masivas en códigos largos, `qcode` pregunta qué parte específica deseas entender, optimizando el tiempo y el uso de tokens.


### 6. Sistema de Instalación (`cmd_qia_install`)
- Crea enlaces simbólicos en `~/bin/` para `q`, `qcode`, `qia`, etc., apuntando todos al mismo script `qia.py`.
- Crea un "wrapper" especial para `qdo` que define la variable de entorno `QIA_INVOKED_AS` para disparar la lógica de ejecución Bash.

---

## Guía para IAs (Contexto de Sistema)

Si eres una IA trabajando en este código:
- **Estructura:** El código es monolítico por diseño para facilitar la portabilidad.
- **Comunicación:** Usa `urllib.request` (sin dependencias externas) para hablar con el puerto 8080.
- **Prompts:** El éxito de `qdo` depende de la rigidez del `system_prompt`. Si el modelo alucina texto, la función `handle_qdo` debe ser el filtro final.
- **Seguridad:** `qdo` ejecuta comandos directamente si el usuario pulsa 'e'. La precisión en la síntesis es vital.

## Uso Rápido

- `q "pregunta"`: Chat rápido.
- `qdo "acción"`: Genera comando -> Ejecuta/Refina/Explica.
- `qcode "tarea"`: Genera código.
- `qia status`: Ver estado del backend y configuración.
