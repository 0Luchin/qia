# QIA v2 - IA para LARLAB 🚀

Asistente técnico especializado en infraestructura, redes (NOC) y desarrollo, optimizado para ejecutarse localmente con un consumo mínimo de recursos.

## 🛠️ Herramientas Principales

- **`q`**: Consultas técnicas rápidas. Respuestas directas y precisas (máximo 2 párrafos).
- **`qdo`**: Sintetizador de comandos Bash. 
    - ✨ **Novedad v2**: Menú interactivo para **Ejecutar**, **Refinar**, **Explicar** o **Cancelar**.
- **`qcode`**: Generador de código fuente.
    - ✨ **Novedad v2**: Menú interactivo para **Guardar** (con detección de extensión y creación de rutas), **Refinar**, **Explicar** partes específicas o **Cancelar**.

## ⚙️ Gestión y Configuración

- **`qia help`**: Muestra el manual visual de uso.
- **`qia status`**: Información sobre el backend, modelo activo y perfil.
- **`qia stop`**: Detiene el servidor `llama-server`.
- **`qmodel`**: Lista modelos disponibles o cambia el modelo activo.
- **`qprofile`**: Cambia el perfil de respuesta (`terminal`, `noc`, `python`).
- **`qia install`**: Configura automáticamente todos los symlinks en `~/bin`.

## 🚀 Instalación Rápida

1. Asegúrate de tener `llama-server` en `~/local-llm/llama.cpp/build/bin/`.
2. Coloca tus modelos GGUF en `~/local-llm/models/qwen2.5-coder-3b/`.
3. Ejecuta la instalación de links:
   ```bash
   python3 qia.py install
   ```

## 🏗️ Arquitectura (v2.0.0)

QIA v2 ha sido reescrito para ser un único script monolítico robusto:
- **Backend**: Integración nativa con la API de `llama.cpp` (OpenAI compatible).
- **UI**: Logos animados ANSI, colores dinámicos y manejo avanzado de señales (`Ctrl+C`).
- **Filtrado**: Extracción inteligente de código y comandos, eliminando el ruido del LLM (markdown, explicaciones no pedidas).

---
*Desarrollado para LARLAB - 2026*
