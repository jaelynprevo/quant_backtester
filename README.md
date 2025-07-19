# Cloud-Deployed Quant Backtester

## Overview  
End-to-end platform:  
1. Ingest historical crypto/equity data → PostgreSQL  
2. Run momentum & mean-reversion backtests → output metrics  
3. Serve results via Streamlit dashboard  
4. Schedule with Airflow, deploy on AWS ECS/EKS

## Setup  
1. `docker-compose up --build`  
2. Visit `http://localhost:8501` for dashboard  
3. Airflow UI: `http://localhost:8080`
