# QIA - Query Artificial Intelligence 🚀

**QIA** es un asistente de IA local de alto rendimiento diseñado para la terminal. Proporciona soporte técnico instantáneo, genera comandos Bash ejecutables y escribe código fuente—todo ejecutándose 100% localmente en tu máquina mediante `llama.cpp`.

---

## ✨ Características Principales

- **Privacidad Total:** Tus datos nunca salen de tu máquina. La inferencia es local.
- **Velocidad Extrema:** Optimizado para modelos pequeños y potentes (como Qwen2.5-Coder) para respuestas casi instantáneas.
- **Perfiles Especializados:** Comportamientos ajustados para SysAdmins, Desarrolladores e Ingenieros de NOC.
- **UI Interactiva:** Interfaz de terminal colorida con paletas personalizadas y animaciones.

---

## 🛠️ Modos de Operación

QIA está diseñado para ser invocado a través de tres alias principales:

*   **`q "tu pregunta"`**: Consultas técnicas generales. Respuestas breves y directas.
*   **`qdo "descripción de tarea"`**: Genera comandos Bash ejecutables. Incluye opciones para **Ejecutar**, **Refinar** o **Explicar** el comando.
*   **`qcode "descripción lógica"`**: Genera código fuente puro. Permite guardar la salida directamente en un archivo.

---

## 👤 Perfiles Especializados

| Perfil | Enfoque | Ideal para... |
| :--- | :--- | :--- |
| **`terminal`** (Default) | Linux/Bash/Python General | Tareas diarias y resolución rápida de problemas. |
| **`noc`** | Redes e Infraestructura | Diagnósticos de red, seguridad y gestión de infra. |
| **`python`** | Desarrollo Senior en Python | Código limpio, algoritmos eficientes y depuración. |

*Cambia de perfil con: `qia profile <nombre>`*

---

## 🎨 Personalización

QIA incluye un sistema de colores dinámico para adaptarse a la estética de tu terminal:

- **Modo Interactivo:** Ejecuta `qia color` para abrir el probador visual. Usa `+` y `-` para navegar por 21 paletas (0-20).
- **Selección Directa:** `qia color 12` o `qia color random`.
- **Minimalista:** `qia color 0` para un estilo limpio en escala de grises.

---

## ⚙️ Comandos del Sistema

*   **`qia status`**: Verifica el estado del backend, modelo activo y perfil.
*   **`qia doctor`**: Ejecuta un diagnóstico completo de dependencias y entorno.
*   **`qia install`**: Reinstala o verifica la configuración local.
*   **`qia model`**: Lista o cambia entre modelos GGUF descargados.
*   **`qia stop`**: Detiene el servidor de inferencia local.
*   **`qia update`**: Descarga la última versión directamente desde el repositorio.

---

## 🚀 Inicio Rápido

1.  **Clonar e Instalar:**
    ```bash
    git clone https://github.com/0Luchin/qia.git
    cd qia
    make install
    ```
2.  **Verificar:**
    ```bash
    qia doctor
    ```
3.  **Preguntar algo:**
    ```bash
    q "Como reviso los puertos abiertos en Linux?"
    ```

---

## ☕ Apoya el Proyecto

Si QIA te facilita la vida, considera apoyar su desarrollo:

- [PayPal](https://paypal.me/0Luchin)
- [Ko-fi](https://ko-fi.com/0luchin)

---
*Hecho con IA y amor por [0Luchin](https://github.com/0Luchin) para [LARLAB](https://larlab.xyz/) - 2026*
