# QIA - Query Artificial Intelligence 🚀

**QIA** (Query Artificial Intelligence) es un asistente técnico diseñado para la automatización, gestión de infraestructura y generación de código, ejecutado localmente para garantizar **privacidad total** y **velocidad**.

---

## 🛠️ ¿Qué hace QIA?

QIA convierte tu terminal en un asistente experto:

*   **`q`**: Consultas técnicas rápidas. Respuestas directas y precisas.
*   **`qdo`**: Sintetizador de comandos Bash. Incluye menú interactivo para **ejecutar** comandos directamente en tu terminal, **refinarlos** o pedir una **explicación**.
*   **`qcode`**: Generador de código fuente. Incluye herramientas para **guardar** archivos automáticamente con la extensión correcta, **refinar** el código o realizar **explicaciones** por bloques.

---

## 🚀 Instalación

Para instalar QIA, abre tu terminal (Linux/WSL) y sigue estos pasos:

### 1. Preparar el sistema
```bash
sudo apt update
# Necesario para compilar llama.cpp y gestionar el repositorio
sudo apt install -y make wget python3 cmake git build-essential
```

### 2. Instalar QIA
```bash
make install
```
*Nota: La instalación compilará el motor de inferencia (llama.cpp) localmente, por lo que puede tomar unos minutos dependiendo de tu hardware.*

Una vez instalado, escribe `qia status` en tu terminal para verificar que todo funciona correctamente. El backend se ejecuta por defecto en el puerto `18080`.

---

## 🏗️ Organización del Repositorio

- **`/` (Raíz)**: Código fuente, instalador (`Makefile`) y guías.
- **`TECHNICAL.md`**: Detalles técnicos profundos sobre la arquitectura para desarrolladores.

---

## ☕ Donaciones

Si te ha sido útil esta herramienta y quieres apoyar su desarrollo continuo, ¡cualquier aporte es bienvenido!

- [PayPal](https://paypal.me/0Luchin)
- [Ko-fi](https://ko-fi.com/0luchin)

---
*Hecho con IA y mucho amor por [0Luchin](https://github.com/0Luchin) para [LARLAB](https://larlab.xyz/) - 2026*
