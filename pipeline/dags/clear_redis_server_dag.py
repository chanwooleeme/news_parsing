from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import redis
import os

def clear_redis_server():
    r = redis.Redis(
        host=os.environ.get('REDIS_SERVER_HOST', 'redis'),
        port=os.environ.get('REDIS_SERVER_PORT', 6379),
        db=0
    )
    r.flushdb()
    print("✅ Redis cleared!")

with DAG(
    dag_id="clear_redis_server_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    clear_task = PythonOperator(
        task_id="clear_redis_server",
        python_callable=clear_redis_server,
    )
