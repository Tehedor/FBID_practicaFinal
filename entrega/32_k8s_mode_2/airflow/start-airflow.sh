#!/usr/bin/env bash
set -euo pipefail

# AIRFLOW_ROLE: webserver|scheduler|worker|flower|init|cli (default: webserver)
# Broker/backends must be provided via env when using CeleryExecutor:
#   AIRFLOW__CELERY__BROKER_URL, AIRFLOW__CELERY__RESULT_BACKEND
# Init options (optional):
#   _AIRFLOW_DB_UPGRADE=true|false
#   _AIRFLOW_WWW_USER_CREATE=true|false
#   _AIRFLOW_WWW_USER_USERNAME, _AIRFLOW_WWW_USER_PASSWORD, _AIRFLOW_WWW_USER_EMAIL,
#   _AIRFLOW_WWW_USER_FIRSTNAME, _AIRFLOW_WWW_USER_LASTNAME, _AIRFLOW_WWW_USER_ROLE

ROLE="${AIRFLOW_ROLE:-webserver}"

echo "Starting Airflow role: ${ROLE}"

case "$ROLE" in
  webserver)
    exec airflow webserver
    ;;
  scheduler)
    exec airflow scheduler
    ;;
  worker)
    # For k8s where worker may run as root, you can set C_FORCE_ROOT=true in the pod env.
    # Here we just execute the worker; executor/broker must be configured via env.
    exec airflow celery worker
    ;;
  flower)
    exec airflow celery flower
    ;;
  cli)
    exec bash -lc "airflow"
    ;;
  init)
    # Minimal init routine: upgrade DB and optionally create the web user
    if [[ "${_AIRFLOW_DB_UPGRADE:-false}" == "true" ]]; then
      echo "Upgrading Airflow DB..."
      airflow db upgrade
    fi

    if [[ "${_AIRFLOW_WWW_USER_CREATE:-false}" == "true" ]]; then
      USERNAME="${_AIRFLOW_WWW_USER_USERNAME:-airflow}"
      PASSWORD="${_AIRFLOW_WWW_USER_PASSWORD:-airflow}"
      FIRSTNAME="${_AIRFLOW_WWW_USER_FIRSTNAME:-Air}"
      LASTNAME="${_AIRFLOW_WWW_USER_LASTNAME:-Flow}"
      EMAIL="${_AIRFLOW_WWW_USER_EMAIL:-airflow@example.com}"
      ROLE="${_AIRFLOW_WWW_USER_ROLE:-Admin}"

      echo "Creating Airflow user $USERNAME ($ROLE)..."
      airflow users create \
        --username "$USERNAME" \
        --password "$PASSWORD" \
        --firstname "$FIRSTNAME" \
        --lastname "$LASTNAME" \
        --role "$ROLE" \
        --email "$EMAIL"
    fi

    echo "Airflow version:" && airflow version
    ;;
  *)
    echo "Unknown AIRFLOW_ROLE: $ROLE (expected webserver|scheduler|worker|flower|init|cli)" >&2
    exit 1
    ;;
 esac
