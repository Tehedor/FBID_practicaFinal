docker build -t stehedor/airflow-custom:latest .
docker push stehedor/airflow-custom:latest

# docker save stehedor/airflow-custom:latest > airflow-custom.tar
# microk8s ctr image import airflow-custom.tar