# !/usr/bin/env python

import sys, os, re
from os import environ

# Importamos SparkSession directamente.
# Al usar spark-submit, pyspark ya está en el path.
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, IntegerType, FloatType, DoubleType, DateType, TimestampType
from pyspark.sql.types import StructType, StructField
from pyspark.sql.functions import udf, lit, concat
from pyspark.ml.feature import Bucketizer, StringIndexer, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

def main(base_path):
  
  # Gestión de path por defecto
  if not base_path:
    base_path = "."
  
  APP_NAME = "train_spark_mllib_model"
  
  print(f"--- Iniciando Spark App: {APP_NAME} ---")
  print(f"--- Base Path: {base_path} ---")

  # ---------------------------------------------------------
  # 1. INICIALIZACIÓN ESTÁNDAR DE SPARK (FIX)
  # ---------------------------------------------------------
  # Eliminamos findspark. Usamos el builder estándar.
  # Las configuraciones de memoria y master vienen del spark-submit.
  spark = SparkSession.builder \
      .appName(APP_NAME) \
      .getOrCreate()
  
  # Opcional: bajar el nivel de log para que no ensucie la consola
  spark.sparkContext.setLogLevel("WARN")
  
  print("--- SparkSession creada exitosamente ---")
  # ---------------------------------------------------------

  # Definición del Esquema
  schema = StructType([
    StructField("ArrDelay", DoubleType(), True),
    StructField("CRSArrTime", TimestampType(), True),
    StructField("CRSDepTime", TimestampType(), True),
    StructField("Carrier", StringType(), True),
    StructField("DayOfMonth", IntegerType(), True),
    StructField("DayOfWeek", IntegerType(), True),
    StructField("DayOfYear", IntegerType(), True),
    StructField("DepDelay", DoubleType(), True),
    StructField("Dest", StringType(), True),
    StructField("Distance", DoubleType(), True),
    StructField("FlightDate", DateType(), True),
    StructField("FlightNum", StringType(), True),
    StructField("Origin", StringType(), True),
  ])
  
  input_path = "{}/data/simple_flight_delay_features.jsonl.bz2".format(base_path)
  print(f"--- Leyendo datos desde: {input_path} ---")
  
  try:
      features = spark.read.json(input_path, schema=schema)
      # Forzamos una acción para verificar que lee bien
      print(f"Total registros leídos: {features.count()}")
  except Exception as e:
      print(f"ERROR LEYENDO DATOS: {e}")
      sys.exit(1)

  #
  # Check for nulls
  #
  print("--- Verificando nulos ---")
  # Nota: Esta operación puede ser costosa, úsala con cuidado en producción
  # null_counts = [(column, features.where(features[column].isNull()).count()) for column in features.columns]
  # cols_with_nulls = filter(lambda x: x[1] > 0, null_counts)
  # print(list(cols_with_nulls))
  
  #
  # Add a Route variable
  #
  features_with_route = features.withColumn(
    'Route',
    concat(
      features.Origin,
      lit('-'),
      features.Dest
    )
  )
  
  #
  # Bucketizer
  #
  splits = [-float("inf"), -15.0, 0, 30.0, float("inf")]
  arrival_bucketizer = Bucketizer(
    splits=splits,
    inputCol="ArrDelay",
    outputCol="ArrDelayBucket"
  )
  
  # Save the bucketizer
  arrival_bucketizer_path = "{}/models/arrival_bucketizer_2.0.bin".format(base_path)
  print(f"--- Guardando Bucketizer en: {arrival_bucketizer_path} ---")
  arrival_bucketizer.write().overwrite().save(arrival_bucketizer_path)
  
  # Apply the bucketizer
  ml_bucketized_features = arrival_bucketizer.transform(features_with_route)
  
  #
  # StringIndexer
  #
  for column in ["Carrier", "Origin", "Dest", "Route"]:
    string_indexer = StringIndexer(
      inputCol=column,
      outputCol=column + "_index"
    )
    
    string_indexer_model = string_indexer.fit(ml_bucketized_features)
    ml_bucketized_features = string_indexer_model.transform(ml_bucketized_features)
    
    ml_bucketized_features = ml_bucketized_features.drop(column)
    
    # Save the pipeline model
    string_indexer_output_path = "{}/models/string_indexer_model_{}.bin".format(base_path, column)
    string_indexer_model.write().overwrite().save(string_indexer_output_path)
  
  #
  # VectorAssembler
  #
  numeric_columns = ["DepDelay", "Distance", "DayOfMonth", "DayOfWeek", "DayOfYear"]
  index_columns = ["Carrier_index", "Origin_index", "Dest_index", "Route_index"]
  
  vector_assembler = VectorAssembler(
    inputCols=numeric_columns + index_columns,
    outputCol="Features_vec"
  )
  final_vectorized_features = vector_assembler.transform(ml_bucketized_features)
  
  # Save vector assembler
  vector_assembler_path = "{}/models/numeric_vector_assembler.bin".format(base_path)
  vector_assembler.write().overwrite().save(vector_assembler_path)
  
  # Limpieza de columnas usadas
  for column in index_columns:
    final_vectorized_features = final_vectorized_features.drop(column)
  
  #
  # Random Forest
  #
  print("--- Entrenando Random Forest ---")
  rfc = RandomForestClassifier(
    featuresCol="Features_vec",
    labelCol="ArrDelayBucket",
    predictionCol="Prediction",
    maxBins=4657,
    maxMemoryInMB=1024
  )
  model = rfc.fit(final_vectorized_features)
  
  # Save model
  model_output_path = "{}/models/spark_random_forest_classifier.flight_delays.5.0.bin".format(base_path)
  print(f"--- Guardando modelo en: {model_output_path} ---")
  model.write().overwrite().save(model_output_path)
  
  #
  # Evaluate
  #
  print("--- Evaluando modelo ---")
  predictions = model.transform(final_vectorized_features)
  
  evaluator = MulticlassClassificationEvaluator(
    predictionCol="Prediction",
    labelCol="ArrDelayBucket",
    metricName="accuracy"
  )
  accuracy = evaluator.evaluate(predictions)
  print("Accuracy = {}".format(accuracy))
  
  # Stop Spark
  spark.stop()

if __name__ == "__main__":
  # Validamos argumentos
  if len(sys.argv) > 1:
    base_path = sys.argv[1]
  else:
    print("WARN: No base_path provided, defaulting to /opt/airflow")
    base_path = "/opt/airflow"
    
  main(base_path)