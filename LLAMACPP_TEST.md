# Prueba llama.cpp

Backend probado:

- llama.cpp compilado localmente en WSL
- modelo: qwen2.5-coder-3b-instruct-q4_k_m.gguf
- modo probado: llama-server
- puerto: 127.0.0.1:8080

Resultado:

La API local respondió correctamente en:

http://127.0.0.1:8080/v1/chat/completions

Respuesta de prueba:

netstat -tuln

Conclusión:

llama-server funciona y parece responder más rápido que el flujo anterior con Ollama.
