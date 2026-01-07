apply-kafka:
	@kubectl apply -f 10-kafka.yaml
	@kubectl apply -f 11-init-kafka.yaml

apply-mongo:
	@kubectl apply -f 20-mongo.yaml

apply-spark:
	@kubectl apply -f 30-spark-master.yaml
	@kubectl apply -f 31-spark-worker.yaml
	@kubectl apply -f 32-spark-submit.yaml

apply-python-app:
	@kubectl apply -f 40-python-app.yaml

apply-all: apply-kafka apply-mongo apply-spark apply-python-app