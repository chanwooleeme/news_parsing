from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import redis

def clear_redis_cache():
    r = redis.Redis(host="redis", port=6379, db=0)
    r.flushdb()
    print("✅ Redis cleared!")

with DAG(
    dag_id="redis_cache_clearer",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    clear_task = PythonOperator(
        task_id="clear_redis",
        python_callable=clear_redis_cache,
    )
