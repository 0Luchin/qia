# Makefile para QIA
# Instala QIA y prepara el entorno completo (motor + modelo)

BIN_DIR := $(HOME)/bin
INSTALL_PATH := $(BIN_DIR)/qia.py
LLAMA_DIR := $(HOME)/local-llm/llama.cpp
MODEL_DIR := $(HOME)/local-llm/models/qwen2.5-coder-3b
MODEL_URL := https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf
PORT := 18080
LOG_FILE := install.log
THRESHOLD_GB := 5

# Utilidad para spinner y manejo de errores con log
define run_with_spinner
	@echo "$(1)..."
	@($(2)) >> $(LOG_FILE) 2>&1 & pid=$$!; 
	while [ -d /proc/$$pid ]; do 
		for char in '-' '' '|' '/'; do 
			printf "  $$char "; 
			sleep 0.1; 
		done; 
	done; 
	wait $$pid; 
	if [ $$? -ne 0 ]; then 
		echo "

❌ ERROR: $(1) falló. Revisa '$(LOG_FILE)' para más detalles."; 
		exit 1; 
	else 
		echo "✅ $(1) completado.   "; 
	fi
endef

install: check_deps check_disk build_llama download_model install_qia
	@echo "--- ¡Instalación exitosa! ---"
	@rm -f $(LOG_FILE)

check_deps:
	@echo "--- Verificando dependencias ---"
	@for cmd in git cmake make g++ python3; do 
		if ! command -v $$cmd > /dev/null 2>&1; then 
			echo "❌ Error: $$cmd no está instalado. Ejecuta: sudo apt install $$cmd"; 
			exit 1; 
		fi; 
	done
	@echo "✅ Todas las dependencias encontradas."

check_disk:
	@echo "--- Verificando espacio en disco ---"
	@AVAILABLE_GB=$$(df -BG ~ | tail -1 | awk '{print $$4}' | sed 's/G//'); 
	if [ $$AVAILABLE_GB -lt $(THRESHOLD_GB) ]; then 
		echo "❌ Error: Espacio insuficiente. Necesitas al menos $(THRESHOLD_GB)GB libres."; 
		exit 1; 
	fi
	@echo "✅ Espacio en disco suficiente."

build_llama:
	@echo "--- Preparando llama.cpp ---"
	mkdir -p $(HOME)/local-llm
	@if [ ! -d $(LLAMA_DIR) ]; then 
		$(call run_with_spinner,Clonando repositorio,git clone https://github.com/ggerganov/llama.cpp $(LLAMA_DIR)); 
	fi
	$(call run_with_spinner,Compilando motor,cd $(LLAMA_DIR) && mkdir -p build && cd build && cmake .. && make -j$$(nproc --ignore=1 2>/dev/null || echo 1))

download_model:
	@echo "--- Preparando modelo ---"
	mkdir -p $(MODEL_DIR)
	@if [ ! -f $(MODEL_DIR)/qwen2.5-coder-3b-instruct-q4_k_m.gguf ]; then 
		$(call run_with_spinner,Descargando modelo,wget --continue --tries=3 --timeout=30 -O $(MODEL_DIR)/qwen2.5-coder-3b-instruct-q4_k_m.gguf $(MODEL_URL)); 
	fi

install_qia:
	@echo "--- Instalando QIA ---"
	mkdir -p $(BIN_DIR)
	mkdir -p $(HOME)/.config/qia
	@if [ ! -f $(HOME)/.config/qia/port ]; then echo $(PORT) > $(HOME)/.config/qia/port; fi
	cp qia.py $(INSTALL_PATH)
	chmod +x $(INSTALL_PATH)
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/q
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/qcode
	ln -sf $(INSTALL_PATH) $(BIN_DIR)/qia
	echo '#!/usr/bin/env bash' > $(BIN_DIR)/qdo
	echo 'QIA_INVOKED_AS=qdo python3 $(INSTALL_PATH) "$$@"' >> $(BIN_DIR)/qdo
	chmod +x $(BIN_DIR)/qdo
	@echo "--- Verificando PATH ---"
	@if ! echo $$PATH | grep -q "$(BIN_DIR)"; then echo "AVISO: $(BIN_DIR) no está en tu PATH. Añádelo agregando esto a tu ~/.bashrc o ~/.zshrc:" && echo 'export PATH="$$HOME/bin:$$PATH"'; fi

clean:
	rm -f $(BIN_DIR)/q $(BIN_DIR)/qcode $(BIN_DIR)/qia $(BIN_DIR)/qdo $(INSTALL_PATH) $(LOG_FILE)
	rm -rf $(LLAMA_DIR)
