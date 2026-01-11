FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY web /app/web

WORKDIR /app/web

EXPOSE 5001

CMD ["python", "predict_flask.py"]