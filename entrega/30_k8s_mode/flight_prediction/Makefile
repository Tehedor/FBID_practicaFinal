# scala 2.12.10
# spark 3.5.3
# java 17.0.14-amzn (SDKMAN!)
# python 3.7 (mise/rtx)

SHELL := /bin/bash
SDKMAN_INIT := $(HOME)/.sdkman/bin/sdkman-init.sh
MISE_INIT := $(HOME)/.local/share/mise/init.sh # Ruta común, ajusta si es necesario

JAVA_VERSION  := 17.0.14-amzn
SCALA_VERSION := 2.12.10
SPARK_VERSION := 3.5.3
PYTHON_VERSION := 3.7

VERSION_FILE := .previous-versions

.PHONY: install
install:
	@echo "Instalando Java, Scala, Spark con SDKMAN!..."
	@source $(SDKMAN_INIT) && \
	sdk install java $(JAVA_VERSION) && \
	sdk install scala $(SCALA_VERSION) && \
	sdk install spark $(SPARK_VERSION)
	@echo "Instalando Python con mise!..."
	# Mise/rtx se encarga de instalar las herramientas listadas en .tool-versions
	@mise install python@$(PYTHON_VERSION) # Asegúrate de que tienes .tool-versions configurado
	@echo "✓ Instalación completada. Ahora ejecuta 'make init' para configurar."

.PHONY: init
init:
	@echo "Guardando versiones actuales..."
	# Guardar versiones actuales en un solo archivo
	@source $(SDKMAN_INIT) && \
	echo "JAVA: $$(sdk current java 2>/dev/null | awk '{print $$4}')" > $(VERSION_FILE)
	@source $(SDKMAN_INIT) && \
	echo "SCALA: $$(sdk current scala 2>/dev/null | awk '{print $$4}')" >> $(VERSION_FILE)
	@source $(SDKMAN_INIT) && \
	echo "SPARK: $$(sdk current spark 2>/dev/null | awk '{print $$4}')" >> $(VERSION_FILE)
	@echo "PYTHON: $$(mise current python 2>/dev/null | awk '{print $$NF}')" >> $(VERSION_FILE)
	@echo "Archivo de versiones anteriores guardado en $(VERSION_FILE)"
	
	@echo "Activando versiones requeridas..."
	# Activar versiones con SDKMAN!
	@source $(SDKMAN_INIT) && \
	sdk use java $(JAVA_VERSION) && \
	sdk use scala $(SCALA_VERSION) && \
	sdk use spark $(SPARK_VERSION)
	
	# Activar versión con mise (crea el entorno local)
	@mise use python@$(PYTHON_VERSION)
	
	@echo "✓ Versiones configuradas y activadas correctamente."

.PHONY: restore
restore:
	@if [ ! -f $(VERSION_FILE) ]; then \
		echo "✗ No hay versiones anteriores guardadas en $(VERSION_FILE). Ejecuta 'make init' primero."; \
		exit 1; \
	fi
	@echo "Restaurando versiones anteriores..."
	
	@source $(SDKMAN_INIT) && \
	JAVA_VER=$$(grep JAVA $(VERSION_FILE) | awk '{print $$2}'); \
	SCALA_VER=$$(grep SCALA $(VERSION_FILE) | awk '{print $$2}'); \
	SPARK_VER=$$(grep SPARK $(VERSION_FILE) | awk '{print $$2}'); \
	PYTHON_VER=$$(grep PYTHON $(VERSION_FILE) | awk '{print $$2}'); \
	
	if [ "$$JAVA_VER" != "none" ]; then sdk use java $$JAVA_VER; fi; \
	if [ "$$SCALA_VER" != "none" ]; then sdk use scala $$SCALA_VER; fi; \
	if [ "$$SPARK_VER" != "none" ]; then sdk use spark $$SPARK_VER; fi; \
	if	[ "$$PYTHON_VER" != "none" ]; then mise use python@$$PYTHON_VER; fi;
	
# 	# Restaurar Python con mise (esto requiere más lógica, mejor dejar que mise maneje el entorno por defecto)
# 	@echo "Nota: Restauración de Python no implementada, mise mantiene su propia versión global/por defecto."
	
	@echo "✓ Versiones SDKMAN! restauradas"



# Compilación del proyecto flight_prediction con sbt
.PHONY: build-flight-prediction
build-flight-prediction:
	@echo "Compilando proyecto flight_prediction con sbt..."
	cd flight_prediction && sbt clean package && \
	sbt package && \
	echo "✓ Compilación completada."
