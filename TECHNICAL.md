# QIA Technical Deep Dive 🛠️

QIA is a modular terminal orchestrator designed for low-latency interaction with local Large Language Models (LLMs). It leverages `llama.cpp` as its inference engine and implements a custom client-server architecture to manage background processes and user interaction.

---

## 🏗️ System Architecture

### 1. The Monolithic Orchestrator (`qia.py`)
Despite being a single file, the architecture is strictly decoupled into functional classes:
- **`QIAConfig`**: Manages persistence in `~/.config/qia/`. Handles configuration for models, profiles, timeouts, and UI preferences.
- **`QIAVisuals`**: A dedicated UI layer. It uses ANSI escape sequences for cursor manipulation and dynamic color rendering based on active palettes.
- **`QIABackend`**: Controls the lifecycle of the inference server. It includes logic for automatic startup, health checks (OpenAI-compatible `/v1/models` endpoint), and process termination.

### 2. Activity & Lifecycle Management (`qia_watcher`)
QIA implements an automatic power-saving mechanism. When the backend starts, it spawns a detached background process (`qia_watcher`) that:
- Monitors `~/.config/qia/last_activity`.
- Compares the last activity timestamp with the user-defined `timeout`.
- Terminstes `llama-server` if the system is idle to free up CPU/GPU resources.

---

## 🎨 Visual Engine & UI Logic

### Dynamic Palettes
QIA uses a "Tertiary Color System" (Primary, Secondary, Tertiary). The `PALETTES` dictionary contains 21 distinct schemes (0-20). 
- **Palette 0**: High-contrast grayscale for minimalist environments.
- **Palettes 1-20**: Various high-visibility schemes (Neon, Cyber, Matrix, Flame, etc.).

### Interactive Terminal Control
The `animate_color_tester` and `cmd_qia_status` functions use raw terminal modes via `tty` and `termios`. This allows:
- **Zero-latency input:** Capturing keys like `+`, `-`, or `Enter` without requiring the user to press Return.
- **Non-destructive UI:** Redrawing specific blocks of the terminal screen while keeping the background stable.

---

## 🧠 Inference & Prompt Engineering

### Multi-Alias Dispatch
QIA behaves differently based on how it is invoked (`sys.argv[0]`):
- **`q` (Query)**: Balanced temperature (~0.6). Direct technical responses.
- **`qdo` (Do)**: Low temperature (~0.01). Strict system prompt to ensure executable output without Markdown.
- **`qcode` (Code)**: Moderate temperature (~0.2). Focused on source code generation with direct-to-file saving capabilities.

### OpenAI Compatibility
The system is built to be backend-agnostic as long as the server follows the OpenAI Chat Completions API. It currently streams tokens in real-time for a "typing" effect.

---

## 🛠️ Internal Data Flow

1. **Invocation**: The user runs a command (e.g., `qdo "list files"`).
2. **Environment Check**: `QIABackend.ensure()` checks if the server is alive. If not, it boots `llama-server` with the configured model.
3. **Prompt Assembly**: `get_system_prompt(mode)` fetches the active profile (Terminal, NOC, or Python) and wraps the user input.
4. **Streaming Inference**: Tokens are requested via `urllib.request`. `qia.py` filters out potential Markdown artifacts (like code blocks) for `qdo` and `qcode` modes.
5. **Action Loop**: For `qdo`/`qcode`, the user enters an interactive loop to Execute, Refine, or Explain the result.

---

## 📂 File System Map

- `~/.config/qia/`: Configuration files (model, port, timeout, palette).
- `~/.local/share/qia/logs/`: Backend logs (`llama-server.log`).
- `~/local-llm/models/`: Storage for GGUF model files.
- `~/bin/qia.py`: The executable installation path.

---
*Technical documentation updated for v2.0.4 - 2026*
