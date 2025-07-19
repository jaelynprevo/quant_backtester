FROM python:3.10-slim
WORKDIR /app

RUN pip install --no-cache-dir requests pandas sqlalchemy psycopg2-binary

COPY ingestion.py .

CMD ["python3", "ingestion.py"]
