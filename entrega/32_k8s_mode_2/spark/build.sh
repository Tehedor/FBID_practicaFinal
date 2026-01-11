docker build -t stehedor/spark-custom_v2:latest .
docker push stehedor/spark-custom_v2:latest

# docker save stehedor/spark-custom:latest > spark-custom.tar
# microk8s ctr image import spark-custom.tar