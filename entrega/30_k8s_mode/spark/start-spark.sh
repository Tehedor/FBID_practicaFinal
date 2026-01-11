#!/usr/bin/env bash
set -euo pipefail

# SPARK_ROLE: master|worker (default: master)
# SPARK_MASTER_URL (for worker): e.g. spark://spark-master:7077
# Optional: SPARK_WORKER_WEBUI_PORT, SPARK_MASTER_HOST, SPARK_MASTER_PORT

ROLE="${SPARK_ROLE:-master}"

echo "Starting Spark role: ${ROLE}"

if [[ "$ROLE" == "master" ]]; then
  : "${SPARK_MASTER_HOST:=spark-master}"
  : "${SPARK_MASTER_PORT:=7077}"
  : "${SPARK_MASTER_WEBUI_PORT:=8080}"
  export SPARK_MASTER_HOST SPARK_MASTER_PORT SPARK_MASTER_WEBUI_PORT
  exec /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master

elif [[ "$ROLE" == "worker" ]]; then
  MASTER_URL="${SPARK_MASTER_URL:-spark://spark-master:7077}"
  : "${SPARK_WORKER_WEBUI_PORT:=8080}"
  export SPARK_WORKER_WEBUI_PORT
  exec /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker "$MASTER_URL"

else
  echo "Unknown SPARK_ROLE: $ROLE (expected 'master' or 'worker')" >&2
  exit 1
fi
