# airflow/dags/quant_backtest.py
import sys
sys.path.insert(0, "/opt/airflow/data_ingestion")  # so we can import ingestion.fetch_agg_bars

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

from ingestion import fetch_agg_bars   # your existing ingestion function

default_args = {
    'owner': 'you',
    'depends_on_past': False,
    'retries': 5,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(hours=1),
}

with DAG(
    dag_id="quant_backtest",
    default_args=default_args,
    description="Daily data pull + backtest (2yr backfill)",
    start_date=datetime(2023, 7, 16),   # two years ago if you like, or pick today
    schedule_interval="@daily",
    catchup=True,
    max_active_runs=1,
) as dag:

    # def ingest(execution_date, **ctx):
    #     d = execution_date.date().isoformat()
    #     # Pull exactly that day’s data via your ingestion function
    #     fetch_agg_bars('AAPL', d, d)
    def ingest(execution_date, **ctx):
        d = execution_date.date().isoformat()
        df = fetch_data('AAPL', d, d)
        save_to_db(df, table="aapl_minute_bars")

    ingest_task = PythonOperator(
        task_id="ingest_data",
        python_callable=ingest,
        provide_context=True,
    )

    # NOTE: no more Python import of backtest; just call the script
    backtest_task = BashOperator(
        task_id="run_backtester",
        bash_command="python3 /opt/airflow/backtester/backtest.py",
    )

    ingest_task >> backtest_task
