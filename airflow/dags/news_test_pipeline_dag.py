from datetime import datetime, timedelta
import logging
import os
from typing import Dict, Any
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator


from airflow.decorators import dag, task
from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

# RSS 피드 모듈 가져오기
from rss_feed.feed_parser import FeedParser

# indexer 모듈 가져오기
from indexer import NewsIndexer

# 환경 변수 설정
os.environ["RSS_FEED_HTML_DIR"] = os.getenv("RSS_FEED_HTML_DIR", "/opt/airflow/data/html")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
os.environ["QDRANT_HOST"] = os.getenv("QDRANT_HOST", "")
os.environ["QDRANT_API_KEY"] = os.getenv("QDRANT_API_KEY", "")

# DAG 기본 파라미터
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 테스트 환경 설정
TARGET_PUBLISHERS = ["경향신문", "뉴시스"]
MAX_HTML_PER_PUBLISHER = 5
EXCLUDED_NEWSPAPERS = []  # 테스트에서는 제외 신문사 없음


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def process_feeds_test() -> Dict[str, Any]:
    """지정된 발행사에서 제한된 수의 HTML 파일을 수집하는 테스트 함수"""
    parser = FeedParser()
    parser.process_feeds_for_test(
        target_publishers=TARGET_PUBLISHERS,
        max_html_per_publisher=MAX_HTML_PER_PUBLISHER
    )
    logging.info(f"테스트 RSS 피드 처리 완료")


def index_articles():
    """HTML 파일을 파싱하고 임베딩하여 저장합니다."""
    # indexer 패키지의 실시간 파이프라인 함수 사용
    indexer = NewsIndexer()
    indexer.process_articles()
    logging.info("임베딩 및 저장 완료")


def upload_and_cleanup_html(html_dir: str, bucket_name: str):
    print(f"[DEBUG] HTML 폴더에 있는 파일 확인: {html_dir}")
    for root, _, files in os.walk(html_dir):
        for file in files:
            print("    - ", os.path.join(root, file))
            
    s3 = S3Hook(aws_conn_id="aws_default")
    html_files_uploaded = 0

    for root, _, files in os.walk(html_dir):
        for file in files:
            if not file.endswith(".html"):
                continue

            local_path = os.path.join(root, file)
            # 상대 경로 기준으로 S3 key 설정 (예: 경향신문/abc123.html)
            relative_path = os.path.relpath(local_path, html_dir)
            s3_key = relative_path.replace("\\", "/")  # for Windows compatibility

            try:
                s3.load_file(
                    filename=local_path,
                    key=s3_key,
                    bucket_name=bucket_name,
                    replace=True
                )
                os.remove(local_path)  # 업로드 성공 시 삭제
                html_files_uploaded += 1
                print(f"✅ 업로드 및 삭제 완료: {s3_key}")
            except Exception as e:
                print(f"❌ 업로드 실패: {s3_key}, 오류: {e}")

    print(f"📦 총 {html_files_uploaded}개 HTML 파일 업로드 및 정리 완료")

    

with DAG(
    'news_pipeline_dag_test',
    default_args=default_args,
    description='뉴스 파이프라인 테스트',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=['rss', 'html', 'parser', 'news', 'embedding'],
) as dag:

    # RSS 피드 처리 태스크
    process_feeds_task = PythonOperator(
        task_id='process_feeds',
        python_callable=process_feeds_test,
    )
    
    index_articles_task = PythonOperator(
        task_id='index_articles',
        python_callable=index_articles,
    )
    
    upload_task = PythonOperator(
        task_id='upload_and_cleanup_html',
        python_callable=upload_and_cleanup_html,
        op_kwargs={
            'html_dir': os.environ["RSS_FEED_HTML_DIR"],
            'bucket_name': os.environ["AWS_S3_BUCKET"]
        }
    )


    # 태스크 의존성 설정
    process_feeds_task >> index_articles_task >> upload_task
    