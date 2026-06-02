# QIA - Query Artificial Intelligence 🚀

**QIA** (Query Artificial Intelligence) is a technical assistant designed for automation, infrastructure management, and code generation, running locally to ensure **total privacy** and **speed**.

---

## 🛠️ What does QIA do?

QIA turns your terminal into an expert assistant:

*   **`q`**: Rapid technical queries. Direct and precise answers.
*   **`qdo`**: Bash command synthesizer. Includes an interactive menu to **execute** commands directly in your terminal, **refine** them, or request an **explanation**.
*   **`qcode`**: Source code generator. Includes tools to **save** files automatically with the correct extension, **refine** the code, or perform **block-based explanations**.

---

## 🚀 Installation

To install QIA, open your terminal (Linux/WSL) and follow these steps:

### 1. Prepare the system
```bash
sudo apt update
# Necessary to compile llama.cpp and manage the repository
sudo apt install -y make wget python3 cmake git build-essential
```

### 2. Install QIA
```bash
make install
```
*Note: The installation will compile the inference engine (llama.cpp) locally, which may take a few minutes depending on your hardware.*

Once installed, type `qia status` in your terminal to verify that everything works correctly. The backend runs on port `18080` by default.

---

## 🏗️ Repository Structure

- **`/` (Root)**: Source code, installer (`Makefile`), and guides.
- **`TECHNICAL.md`**: Deep technical details about the architecture for developers.

---

## ☕ Donations

If you have found this tool useful and want to support its continued development, any contribution is welcome!

- [PayPal](https://paypal.me/0Luchin)
- [Ko-fi](https://ko-fi.com/0luchin)

---
*Made with AI and love by [0Luchin](https://github.com/0Luchin) for [LARLAB](https://larlab.xyz/) - 2026*
