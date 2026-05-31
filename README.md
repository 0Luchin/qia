# qia — asistente de terminal con IA local

Copiloto de terminal que corre modelos de lenguaje localmente vía Ollama.
Sin API keys, sin costos, sin datos que salen de tu máquina.

## Requisitos

- Windows 11 con WSL2 (Ubuntu 22.04 o superior)
- [Ollama](https://ollama.com) instalado en WSL2
- Python 3.10 o superior
- Al menos un modelo descargado (ver abajo)

## Instalación

### 1. Instalar Ollama en WSL2

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verificar que esté corriendo:

```bash
ollama serve &
ollama list
```

### 2. Descargar un modelo

El modelo por defecto es `qwen2.5-coder:3b`. Es el recomendado para empezar:

```bash
ollama pull qwen2.5-coder:3b
```

Otros modelos compatibles:

```bash
ollama pull qwen2.5-coder:7b     # mejor calidad, más lento
ollama pull qwen2.5-coder:1.5b   # más liviano, respuestas rápidas
ollama pull deepseek-coder:1.3b  # alternativa liviana
```

### 3. Clonar el repositorio

```bash
git clone https://github.com/0Luchin/qia.git
cd qia
```

### 4. Instalar los comandos

```bash
chmod +x q qdo qmodel qprofile
sudo cp q qdo qmodel qprofile /usr/local/bin/
```

Verificar:

```bash
q "hola, funcionás?"
```

## Uso

### q — pregunta y respuesta

```bash
q "cómo listo puertos abiertos en Linux"
q "qué hace el comando find -mtime -1"
q "cómo copio un archivo entre directorios en bash"
```

### qdo — genera y ejecuta comandos

Genera un comando, lo muestra y pide confirmación antes de ejecutar.

```bash
qdo "listar archivos modificados en las últimas 24 horas"
qdo "mostrar uso de disco por directorio en /var"
qdo "buscar archivos .log mayores a 100MB"
```

Nunca ejecuta comandos destructivos — tiene lista de bloqueo integrada
que incluye `rm -rf`, `mkfs`, `shutdown`, `curl | sh` y similares.

### qmodel — gestionar modelos

```bash
qmodel              # ver modelo actual
qmodel list         # listar modelos instalados con descripción
qmodel select       # elegir modelo por número
qmodel catalog      # ver modelos sugeridos
qmodel reset        # volver a qwen2.5-coder:3b
```

### qprofile — cambiar el comportamiento

Los perfiles cambian el enfoque del modelo sin tocar el código.

```bash
qprofile            # ver perfil actual
qprofile list       # listar perfiles disponibles
qprofile select     # elegir perfil por número
```

Perfiles disponibles:

| Perfil | Uso |
|--------|-----|
| `terminal` | copiloto general de Linux/WSL (default) |
| `noc` | diagnóstico de red, servicios, logs |
| `bash` | Bash, pipelines y comandos Linux |
| `python` | Python para scripting e infraestructura |
| `reviewer` | revisión conservadora de código |
| `teacher` | explicación técnica paso a paso |
| `custom` | perfil personalizado editable |

Perfil custom:

```bash
qprofile edit       # editar con nano
qprofile custom "Asistente especializado en Docker y contenedores"
```

## Notas

- qia corre 100% local — ningún dato sale de tu máquina
- El portapapeles usa `clip.exe` de Windows — funciona en WSL2
- En Linux nativo reemplazá `clip.exe` por `xclip` en `qia.py`
- En macOS reemplazá `clip.exe` por `pbcopy` en `qia.py`
- Git Bash no es compatible — usar WSL2

## Licencia

MIT
