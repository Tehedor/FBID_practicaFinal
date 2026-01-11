FROM apache/spark:3.5.3

# --------------------------------------------------
# 1️⃣ ROOT para instalación y configuración
# --------------------------------------------------
USER root

ARG APP_HOME=/app

ENV APP_HOME=${APP_HOME} \
    SPARK_HOME=/opt/spark \
    PROJECT_HOME=/opt/airflow \
    PYENV_ROOT=/usr/local/pyenv \
    PYSPARK_PYTHON=/usr/local/pyenv/versions/3.8.19/bin/python3

ENV PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"

# --------------------------------------------------
# 2️⃣ Dependencias del sistema
# --------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    curl \
    ca-certificates \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libffi-dev \
    liblzma-dev \
 && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# 3️⃣ pyenv + Python 3.8.19
# --------------------------------------------------
RUN git clone https://github.com/pyenv/pyenv.git "${PYENV_ROOT}" \
 && "${PYENV_ROOT}/plugins/python-build/install.sh" \
 && /bin/bash -lc "pyenv install -s 3.8.19 && pyenv global 3.8.19"

# --------------------------------------------------
# 4️⃣ Librerías Python (versiones estables)
# --------------------------------------------------
RUN /usr/local/pyenv/versions/3.8.19/bin/python3 -m pip install --no-cache-dir \
    pyspark==3.5.3 \
    numpy==1.21.6 \
    pandas==1.3.5 \
    scikit-learn==1.0.2 \
    pymongo

# --------------------------------------------------
# 5️⃣ CREAR USUARIO REAL (🔥 CLAVE PARA HADOOP 🔥)
# --------------------------------------------------
RUN groupadd -g 0 airflow || true && \
    useradd -u 50000 -g 0 -m -d /opt/airflow -s /bin/bash airflow || true

# --------------------------------------------------
# 6️⃣ Directorios necesarios
# --------------------------------------------------
RUN mkdir -p \
    /opt/airflow/dags \
    /opt/airflow/logs \
    /opt/airflow/plugins \
    /opt/airflow/resources \
    /opt/airflow/data \
    ${APP_HOME}/models \
    /opt/spark/work \
    /opt/spark/logs \
    /opt/spark/ivy

# --------------------------------------------------
# 7️⃣ Permisos (compatibles con K8s / OpenShift)
# --------------------------------------------------
RUN chown -R 50000:0 \
      /opt/airflow \
      /opt/spark/work \
      /opt/spark/logs \
      /opt/spark/ivy \
      ${APP_HOME} \
 && chmod -R 775 \
      /opt/airflow \
      /opt/spark/work \
      /opt/spark/logs \
      /opt/spark/ivy \
      ${APP_HOME}

# --------------------------------------------------
# 8️⃣ Script de arranque
# --------------------------------------------------
COPY start-spark.sh /usr/local/bin/start-spark.sh
RUN chmod +x /usr/local/bin/start-spark.sh

# --------------------------------------------------
# 9️⃣ Usuario final (YA EXISTE EN /etc/passwd)
# --------------------------------------------------
USER 50000

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/start-spark.sh"]
