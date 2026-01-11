FROM apache/airflow:2.1.4

USER root

# ------------------------------------------------------------
# 1. FIX CRÍTICO PARA DEBIAN BUSTER (EOL)
# ------------------------------------------------------------
# Como Debian 10 es antiguo, cambiamos los repositorios a "archive" 
# y desactivamos la verificación de validez de fecha.
RUN echo "deb http://archive.debian.org/debian buster main" > /etc/apt/sources.list && \
    echo "deb http://archive.debian.org/debian-security buster/updates main" >> /etc/apt/sources.list && \
    apt-get -o Acquire::Check-Valid-Until=false update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# 2. INSTALACIÓN ROBUSTA (Sin SDKMAN)
# ------------------------------------------------------------
# Usamos descarga directa porque SDKMAN falla mucho en Docker
# y complica las rutas (ENV).

ENV JAVA_VERSION=17.0.14
ENV SCALA_VERSION=2.12.10
ENV SPARK_VERSION=3.5.3
ENV HADOOP_VERSION=3



# Instalar Java 17 (Amazon Corretto)
RUN wget https://corretto.aws/downloads/resources/17.0.14.7.1/amazon-corretto-17.0.14.7.1-linux-x64.tar.gz -O /tmp/java.tar.gz && \
    mkdir -p /usr/lib/jvm/java-17-amazon-corretto && \
    tar -xvf /tmp/java.tar.gz -C /usr/lib/jvm/java-17-amazon-corretto --strip-components=1 && \
    rm /tmp/java.tar.gz

ENV JAVA_HOME=/usr/lib/jvm/java-17-amazon-corretto
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Instalar Scala
RUN wget https://downloads.lightbend.com/scala/${SCALA_VERSION}/scala-${SCALA_VERSION}.tgz -O /tmp/scala.tgz && \
    mkdir -p /usr/share/scala && \
    tar -xvf /tmp/scala.tgz -C /usr/share/scala --strip-components=1 && \
    rm /tmp/scala.tgz && \
    ln -s /usr/share/scala/bin/scala /usr/bin/scala

# Instalar Spark
RUN wget https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz -O /tmp/spark.tgz && \
    mkdir -p /opt/spark && \
    tar -xvf /tmp/spark.tgz -C /opt/spark --strip-components=1 && \
    rm /tmp/spark.tgz

ENV SPARK_HOME=/opt/spark
ENV PATH="${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"
ENV PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.7-src.zip:${PYTHONPATH}"

# ------------------------------------------------------------
# 3. CONFIGURACIÓN AIRFLOW Y PYTHON
# ------------------------------------------------------------
USER airflow


# Instalamos PySpark para que Python pueda hablar con Spark
RUN pip install --no-cache-dir pyspark==${SPARK_VERSION} findspark

WORKDIR /opt/airflow