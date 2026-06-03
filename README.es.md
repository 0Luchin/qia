# QIA - Query Artificial Intelligence 🚀

**QIA** (Query Artificial Intelligence) es un asistente técnico diseñado para la automatización, gestión de infraestructura y generación de código, ejecutado localmente para garantizar **privacidad total** y **velocidad**.

---

## 🛠️ ¿Qué hace QIA?

QIA convierte tu terminal en un asistente experto:

*   **`q`**: Consultas técnicas rápidas. Respuestas directas y precisas.
    *   *Ejemplo:* `q "¿Cómo puedo ver los puertos abiertos en Linux?"`
*   **`qdo`**: Sintetizador de comandos Bash. Incluye menú interactivo para **ejecutar**, **refinar** o pedir una **explicación**.
    *   *Ejemplo:* `qdo "Busca todos los archivos mayores a 100MB en /var/log"`
*   **`qcode`**: Generador de código fuente. Incluye herramientas para **guardar** archivos, **refinar** el código o realizar **explicaciones**.
    *   *Ejemplo:* `qcode "Crea un script en Python para hacer scraping con BeautifulSoup"`

---

## 🚀 Instalación

Para instalar QIA, simplemente ejecuta en la raíz del repositorio:

```bash
make install
```

*Nota: El instalador verificará dependencias, compilará el motor de inferencia (`llama.cpp`) y descargará el modelo automáticamente si no existen.*

Una vez instalado, usa `qia help` para ver los comandos disponibles.

---

## 🏗️ Organización del Repositorio

- **`scripts/`**: Scripts auxiliares (instalador, etc.).
- **`qia.py`**: Código principal y cliente.
- **`TECHNICAL.md`**: Detalles técnicos profundos.

---

## ☕ Donaciones

Si te ha sido útil esta herramienta y quieres apoyar su desarrollo continuo, ¡cualquier aporte es bienvenido!

- [PayPal](https://paypal.me/0Luchin)
- [Ko-fi](https://ko-fi.com/0luchin)

---
*Hecho con IA y mucho amor por [0Luchin](https://github.com/0Luchin) para [LARLAB](https://larlab.xyz/) - 2026*
