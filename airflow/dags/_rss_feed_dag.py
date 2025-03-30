from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.redis.hooks.redis import RedisHook
import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가 
# PYTHONPATH를 Docker 이미지 생성 시 설정했으므로 필요 없음
# sys.path.append('/opt/airflow')

# rss_feed 모듈에서 FeedParser 클래스 가져오기
from rss_feed.feed_parser import FeedParser

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def process_feeds():
    parser = FeedParser()
    parser.process_feeds()

with DAG(
    'rss_feed_dag',
    default_args=default_args,
    description='RSS 피드 처리 DAG',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=['rss', 'feed'],
) as dag:

    process_feeds_task = PythonOperator(
        task_id='process_feeds',
        python_callable=process_feeds,
    )

    process_feeds_task 