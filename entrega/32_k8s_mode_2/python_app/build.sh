docker build -t stehedor/python_app_flight:latest .
docker push stehedor/python_app_flight:latest

# docker save stehedor/python_app_flight:latest > python_app_flight.tar
# microk8s ctr image import python_app_flight.tar