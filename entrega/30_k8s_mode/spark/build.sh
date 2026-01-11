docker build -t stehedor/spark-custom:latest .
docker push stehedor/spark-custom:latest

# docker save stehedor/spark-custom:latest > spark-custom.tar
# microk8s ctr image import spark-custom.tar