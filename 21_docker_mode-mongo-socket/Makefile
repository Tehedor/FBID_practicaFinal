SHELL := /bin/bash

### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
# Docker Compose control
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
.PHONY: build up down restart logs clean
build:
	@echo "🏗️ Construyendo imágenes de Docker..."
	@docker compose build

up:
	@echo "🚀 Levantando contenedor de Kafka..."
	@docker compose up -d
	@echo "⏳ Esperando unos segundos a que Kafka esté listo..."
	@sleep 5

down:
	@echo "🛑 Deteniendo contenedor..."
	@docker compose down

clean:
	@echo "🗑️ Eliminando contenedores y VOLÚMENES de datos..."
	@docker compose down -v
logs:
	@docker compose logs -f

restart: down up


### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
# Kafka Control
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
CONTAINER_KAFKA := kafka
TOPIC_NAME := flight-delay-ml-request
TOPIC_NAME_RESPONSE := flight-delay-ml-response
KAFKA_SERVER := localhost:9092
KAFKA_BIN_PATH := /opt/kafka/bin

.PHONY: topic-create topic-list topic-clean topic-consumer
topic-create:
	@echo "✨ Creando tópico: $(TOPIC_NAME)..."
	@docker exec $(CONTAINER_KAFKA) $(KAFKA_BIN_PATH)/kafka-topics.sh \
		--create \
		--bootstrap-server $(KAFKA_SERVER) \
		--replication-factor 1 \
		--partitions 1 \
		--topic $(TOPIC_NAME) || echo "El tópico ya existe o hubo un error."

topic-list:
	@echo "📋 Listando tópicos existentes:"
	@docker exec $(CONTAINER_KAFKA) $(KAFKA_BIN_PATH)/kafka-topics.sh --bootstrap-server $(KAFKA_SERVER) --list

topic-clean:
	@echo "🔥 Borrando tópico: $(TOPIC_NAME)..."
	@docker exec $(CONTAINER_KAFKA) $(KAFKA_BIN_PATH)/kafka-topics.sh --delete --topic $(TOPIC_NAME) --bootstrap-server $(KAFKA_SERVER)

topic-consumer-request:
	@echo "👂 Escuchando mensajes en: $(TOPIC_NAME) (Ctrl+C para salir)..."
	@docker exec -it $(CONTAINER_KAFKA) $(KAFKA_BIN_PATH)/kafka-console-consumer.sh \
		--bootstrap-server $(KAFKA_SERVER) \
		--topic $(TOPIC_NAME) \
		--from-beginning

topic-consumer-response:
	@echo "👂 Escuchando mensajes en: $(TOPIC_NAME_RESPONSE) (Ctrl+C para salir)..."
	@docker exec -it $(CONTAINER_KAFKA) $(KAFKA_BIN_PATH)/kafka-console-consumer.sh \
		--bootstrap-server $(KAFKA_SERVER) \
		--topic $(TOPIC_NAME_RESPONSE) \
		--from-beginning



### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
# Spark Control
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
.PHONY: build-flight-prediction
build-flight-prediction:
	@echo "Compilando proyecto flight_prediction con sbt..."
	cd practica_creativa/flight_prediction && sbt clean package && \
	sbt package && \
	echo "✓ Compilación completada."


### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
# WorkFlow
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
