# Makefile para QIA
# Instala QIA y prepara el entorno completo (motor + modelo)

BIN_DIR := $(HOME)/bin
INSTALL_PATH := $(BIN_DIR)/qia.py
LLAMA_DIR := $(HOME)/local-llm/llama.cpp
MODEL_DIR := $(HOME)/local-llm/models/qwen2.5-coder-3b
MODEL_URL := https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf
PORT := 18080

install: build_llama download_model install_qia

build_llama:
	@echo "--- Preparando llama.cpp ---"
	mkdir -p $(HOME)/local-llm
	@if [ ! -d $(LLAMA_DIR) ]; then 
		git clone https://github.com/ggerganov/llama.cpp $(LLAMA_DIR); 
	fi
	cd $(LLAMA_DIR) && mkdir -p build && cd build && cmake .. && make -j

download_model:
	@echo "--- Preparando modelo ---"
	mkdir -p $(MODEL_DIR)
	@if [ ! -f $(MODEL_DIR)/qwen2.5-coder-3b-instruct-q4_k_m.gguf ]; then 
		wget -O $(MODEL_DIR)/qwen2.5-coder-3b-instruct-q4_k_m.gguf $(MODEL_URL); 
	fi

install_qia:
	@echo "--- Instalando QIA ---"
	mkdir -p $(BIN_DIR)
	mkdir -p $(HOME)/.config/qia
	# Guardar puerto configurado solo si no existe
	@if [ ! -f $(HOME)/.config/qia/port ]; then \
		echo $(PORT) > $(HOME)/.config/qia/port; \
	fi
	# Copiar script principal
	cp qia.py $(INSTALL_PATH)
	chmod +x $(INSTALL_PATH)
	# Crear symlinks
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/q
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/qcode
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/qia
	@echo "--- Verificando PATH ---"
	@if ! echo $$PATH | grep -q "$(BIN_DIR)"; then \
		echo "AVISO: $(BIN_DIR) no está en tu PATH. Añádelo agregando esto a tu ~/.bashrc o ~/.zshrc:"; \
		echo 'export PATH="$$HOME/bin:$$PATH"'; \
	fi
	@echo "--- Instalación terminada ---"

clean:
	rm -f $(BIN_DIR)/q $(BIN_DIR)/qcode $(BIN_DIR)/qia $(INSTALL_PATH)
	rm -rf $(LLAMA_DIR)
	# Nota: Se preserva la carpeta de modelos para no borrar descargas pesadas
