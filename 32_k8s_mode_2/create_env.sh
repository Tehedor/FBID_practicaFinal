# !/bin/bash

echo "AIRFLOW_FILESTORE_PATH=$(pwd)/airflow" > .env
echo "MONGO_IMPORT_PATH=$(pwd)/mongo/data" >> .env
echo "SPARK_PATH_SUBMIT_JAR=$(pwd)/flight_prediction/target/scala-2.12/" >> .env
echo "SPARK_PATH_SUBMIT_MODELS=$(pwd)/airflow" >> .env