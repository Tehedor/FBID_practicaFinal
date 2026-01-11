SHELL := /bin/bash
ALL_PROFILES := --profile infra  --profile infraAirflow --profile training --profile prediction

### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
# Docker Compose control
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

.PHONY: build pull pull-build up down restart logs clean
build:
	@echo "🏗️ Construyendo imágenes de Docker..."
	@docker compose $(ALL_PROFILES) build 

pull:
	@echo "⬇️ Descargando imágenes de Docker..."
	@docker compose $(ALL_PROFILES) pull

pull-build: pull build

up-infra:
	@echo "🚀 Levantando contenedor de Kafka..."
	@docker compose --profile infra up -d 
	@echo "⏳ Esperando unos segundos a que Kafka esté listo..."
	@sleep 5

up-airflow:
	@echo "🚀 Levantando contenedor de Airflow..."
	@docker compose --profile infraAirflow up -d --wait
	@echo "⏳ Esperando unos segundos a que Airflow esté listo..."
	@sleep 5

up-training:
	@echo "🚀 Levantando contenedor de Training..."
	@docker compose --profile training up -d 
	@echo "⏳ Esperando unos segundos a que el contenedor de Training esté listo..."
	@sleep 5

up-prediction:
	@echo "🚀 Levantando contenedor de Prediction..."
	@docker compose --profile prediction up -d 
	@echo "⏳ Esperando unos segundos a que el contenedor de Prediction esté listo..."
	@sleep 5

down-infra:
	@echo "🛑 Deteniendo contenedor de Infraestructura..."
	@docker compose --profile infra down 

down-airflow:
	@echo "🛑 Deteniendo contenedor de Airflow..."
	@docker compose --profile infraAirflow down
down-training:
	@echo "🛑 Deteniendo contenedor de Training..."
	@docker compose --profile training down

down-prediction:
	@echo "🛑 Deteniendo contenedor de Prediction..."
	@docker compose --profile prediction down

down-all: down-prediction down-training down-airflow down-infra

clean:
	@echo "🗑️ Eliminando contenedores y VOLÚMENES de datos..."
	@docker compose down -v --profile $(ALL_PROFILES)
logs:
	@docker compose logs -f

restart: down-all up-infra up-airflow up-training up-prediction

### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
# Setup Control
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
.PHONY: download_models download_data
download_models:
	@echo "⬇️ Descargando modelos preentrenados..."
	@cd airflow && \
	mkdir -p models && \
	cd models && \
	curl -Lko ./sklearn_vectorizer.pkl http://s3.amazonaws.com/agile_data_science/sklearn_vectorizer.pkl && \
	curl -Lko ./sklearn_regressor.pkl http://s3.amazonaws.com/agile_data_science/sklearn_regressor.pkl

download_data:
	@echo "⬇️ Descargando datos de vuelos..."
	@cd airflow && \
	mkdir -p data && \
	cd data && \
	curl -Lko ./simple_flight_delay_features.jsonl.bz2 http://s3.amazonaws.com/agile_data_science/simple_flight_delay_features.jsonl.bz2 && \
	curl -Lko ./origin_dest_distances.jsonl http://s3.amazonaws.com/agile_data_science/origin_dest_distances.jsonl

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
