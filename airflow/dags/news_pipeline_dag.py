from datetime import datetime, timedelta
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator

# RSS 피드 모듈 가져오기
from rss_feed.feed_parser import FeedParser

# indexer 모듈 가져오기
from indexer import pipeline


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 제외할 신문사 목록
EXCLUDED_NEWSPAPERS = ['일다', '통일뉴스']

def process_feeds():
    """RSS 피드를 처리하고 HTML 파일을 수집합니다."""
    parser = FeedParser()
    result = parser.process_feeds()
    logging.info(f"RSS 피드 처리 완료: {result}")
    return result

def embedding_feeds():
    """RSS 피드를 임베딩하고 JSONL 파일을 생성합니다."""
    pipeline.run_pipeline()

with DAG(
    'news_pipeline_dag',
    default_args=default_args,
    description='뉴스 파이프라인: RSS 피드 수집, HTML 파싱 및 임베딩',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=['rss', 'html', 'parser', 'news', 'embedding'],
) as dag:

    # RSS 피드 처리 태스크
    process_feeds_task = PythonOperator(
        task_id='process_feeds',
        python_callable=process_feeds,
    )

    
    # 임베딩 처리
    embedding_feeds_task = PythonOperator(
        task_id='run_embedding_pipeline',
        python_callable=embedding_feeds,
    ) 
    
    # 태스크 의존성 설정
    # RSS 피드 처리 -> HTML 파싱 -> 임베딩 JSONL 생성 -> 배치 작업 생성 -> 상태 확인 -> 완료 대기 -> 결과 처리
    process_feeds_task >> embedding_feeds_task