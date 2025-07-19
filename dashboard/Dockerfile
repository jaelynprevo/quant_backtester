# dashboard/Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir \
      streamlit \
      pandas \
      psycopg2-binary \
      sqlalchemy \
      apscheduler \
      altair

COPY app.py .

EXPOSE 8501

ENTRYPOINT ["python3", "-m", "streamlit", "run", "app.py", \
           "--server.port=8501", "--server.address=0.0.0.0"]
