# QIA - Query Artificial Intelligence 🚀

**QIA** is a high-performance, local AI assistant designed for the terminal. It provides instant technical support, generates executable Bash commands, and writes source code—all running 100% locally on your machine using `llama.cpp`.

---

## ✨ Key Features

- **Total Privacy:** Your data never leaves your machine. Inference is performed locally.
- **Extreme Speed:** Optimized for small, powerful models (like Qwen2.5-Coder) for near-instant responses.
- **Context-Aware Profiles:** Specialized behaviors for SysAdmins, Developers, and NOC Engineers.
- **Interactive UI:** Colorful terminal interface with custom palettes and animated feedback.

---

## 🛠️ Modes of Operation

QIA is designed to be invoked through three main aliases:

*   **`q "your question"`**: General technical queries. Brief and direct responses.
*   **`qdo "task description"`**: Generates executable Bash commands. Includes options to **Execute**, **Refine**, or **Explain** the command.
*   **`qcode "logic description"`**: Generates pure source code. Allows you to save the output directly to a file.

---

## 👤 Specialized Profiles

| Profile | Focus | Best for... |
| :--- | :--- | :--- |
| **`terminal`** (Default) | General Linux/Bash/Python | Daily terminal tasks and quick troubleshooting. |
| **`noc`** | Networking & Infrastructure | Network diagnostics, security, and infra management. |
| **`python`** | Senior Python Development | Clean code, efficient algorithms, and debugging. |

*Switch profiles using: `qia profile <name>`*

---

## 🎨 Personalization

QIA features a dynamic color system to match your terminal aesthetics:

- **Interactive Mode:** Run `qia color` to open the visual tester. Use `+` and `-` to cycle through 21 palettes (0-20).
- **Direct Selection:** `qia color 12` or `qia color random`.
- **Minimalist:** `qia color 0` for a clean grayscale look.

---

## ⚙️ System Commands

*   **`qia status`**: Check backend health, active model, and profile.
*   **`qia doctor`**: Run a full diagnostic of dependencies and environment.
*   **`qia install`**: Reinstall or verify the local setup.
*   **`qia model`**: List or switch between downloaded GGUF models.
*   **`qia stop`**: Terminate the local inference server.
*   **`qia update`**: Pull the latest version directly from the repository.

---

## 🚀 Quick Start

1.  **Clone and Install:**
    ```bash
    git clone https://github.com/0Luchin/qia.git
    cd qia
    make install
    ```
2.  **Verify:**
    ```bash
    qia doctor
    ```
3.  **Ask something:**
    ```bash
    q "How do I check open ports in Linux?"
    ```

---

## ☕ Support the Project

If QIA makes your life easier, consider supporting its development:

- [PayPal](https://paypal.me/0Luchin)
- [Ko-fi](https://ko-fi.com/0luchin)

---
*Made with AI and love by [0Luchin](https://github.com/0Luchin) for [LARLAB](https://larlab.xyz/) - 2026*
