# Makefile para QIA v2
# Instala QIA en el sistema local

BIN_DIR := $(HOME)/bin
INSTALL_PATH := $(BIN_DIR)/qia.py
MODEL_DIR := $(HOME)/local-llm/models/qwen2.5-coder-3b
MODEL_URL := https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf

install:
	@echo "--- Instalando QIA v2 ---"
	mkdir -p $(BIN_DIR)
	# Copiar script principal
	cp qia.py $(INSTALL_PATH)
	chmod +x $(INSTALL_PATH)
	# Crear symlinks
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/q
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/qcode
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/qia
	# Crear modelo si no existe
	mkdir -p $(MODEL_DIR)
	@if [ ! -f $(MODEL_DIR)/qwen2.5-coder-3b-instruct-q4_k_m.gguf ]; then \
		echo "Descargando modelo..."; \
		wget -O $(MODEL_DIR)/qwen2.5-coder-3b-instruct-q4_k_m.gguf $(MODEL_URL); \
	fi
	@echo "--- Instalación terminada ---"

clean:
	rm -f $(BIN_DIR)/q $(BIN_DIR)/qcode $(BIN_DIR)/qia $(INSTALL_PATH)
