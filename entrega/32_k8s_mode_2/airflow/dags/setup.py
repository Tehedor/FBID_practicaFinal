import sys, os, re

from airflow import DAG
from airflow.operators.bash import BashOperator

from datetime import datetime, timedelta
import iso8601

PROJECT_HOME = os.getenv("PROJECT_HOME")


default_args = {
  'owner': 'airflow',
  'depends_on_past': False,
  'start_date': iso8601.parse_date("2016-12-01"),
  'retries': 3,
  'retry_delay': timedelta(minutes=5),
}

training_dag = DAG(
  'flight_prediction_training',
  default_args=default_args,
  schedule_interval=None
)

# We use the same two commands for all our PySpark tasks
# ... imports ...

# Modificamos el comando para obtener la IP del Pod de Airflow dinámicamente
# y pasársela a Spark como spark.driver.host
pyspark_bash_command = """
POD_IP=$(hostname -i)

spark-submit --master {{ params.master }} \
  --conf spark.driver.host=$POD_IP \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.executor.memory=512m \
  --conf spark.executor.cores=1 \
  {{ params.base_path }}/{{ params.filename }} \
  {{ params.base_path }}
"""

pyspark_date_bash_command = """
POD_IP=$(hostname -i)

spark-submit --master {{ params.master }} \
  --conf spark.driver.host=$POD_IP \
  --conf spark.driver.bindAddress=0.0.0.0 \
  {{ params.base_path }}/{{ params.filename }} \
  {{ ts }} {{ params.base_path }}
"""

# ... resto del DAG ...


# Gather the training data for our classifier
"""
extract_features_operator = BashOperator(
  task_id = "pyspark_extract_features",
  bash_command = pyspark_bash_command,
  params = {
    "master": "spark://spark-cluster-master:7077",
    "filename": "resources/extract_features.py",
    "base_path": "{}/".format(PROJECT_HOME)
  },
  dag=training_dag
)

"""

# Train and persist the classifier model
train_classifier_model_operator = BashOperator(
  task_id = "pyspark_train_classifier_model",
  bash_command = pyspark_bash_command,
  params = {
    "master": "spark://spark-cluster-master:7077",
    "filename": "resources/train_spark_mllib_model.py",
    "base_path": "{}/".format(PROJECT_HOME)
  },
  dag=training_dag
)

# The model training depends on the feature extraction
#train_classifier_model_operator.set_upstream(extract_features_operator)