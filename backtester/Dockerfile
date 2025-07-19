# backtester/Dockerfile
FROM python:3.10-slim
WORKDIR /app

RUN pip install --no-cache-dir \
      requests \
      pandas \
      sqlalchemy \
      psycopg2-binary \
      backtrader \
      yfinance

COPY backtester/ ./backtester/

COPY data_ingestion/ingestion.py .

# Use module invocation 
ENTRYPOINT ["python3", "-m", "backtester.backtest"]
