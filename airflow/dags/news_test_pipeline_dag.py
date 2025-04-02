from datetime import datetime, timedelta
import logging
import os
import shutil
from airflow import DAG
from airflow.operators.python import PythonOperator
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

# 테스트 환경 설정
TARGET_PUBLISHERS = ["경향신문", "뉴시스"]
MAX_HTML_PER_PUBLISHER = 5

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def process_feeds_test():
    """지정된 발행사에서 제한된 수의 HTML 파일을 수집하는 테스트 함수"""
    parser = FeedParser()
    parser.process_feeds_for_test(
        target_publishers=TARGET_PUBLISHERS,
        max_html_per_publisher=MAX_HTML_PER_PUBLISHER
    )
    logging.info("테스트 RSS 피드 처리 완료")

def index_articles():
    """HTML 파일을 파싱하고 임베딩하여 저장합니다."""
    indexer = NewsIndexer()
    indexer.process_articles()
    logging.info("임베딩 및 저장 완료")

def upload_html_to_s3(html_dir: str, bucket_name: str):
    """HTML 파일을 S3에 업로드"""
    s3 = S3Hook(aws_conn_id="aws_default")
    html_files_uploaded = 0

    for root, _, files in os.walk(html_dir):
        for file in files:
            if not file.endswith(".html"):
                continue

            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, html_dir)
            s3_key = relative_path.replace("\\", "/")

            try:
                s3.load_file(
                    filename=local_path,
                    key=s3_key,
                    bucket_name=bucket_name,
                    replace=True
                )
                html_files_uploaded += 1
                logging.info(f"✅ 업로드 완료: {s3_key}")
            except Exception as e:
                logging.error(f"❌ 업로드 실패: {s3_key}, 오류: {e}")

    logging.info(f"📦 총 {html_files_uploaded}개 HTML 파일 업로드 완료")

def cleanup_html(html_dir: str):
    """HTML 디렉토리 내부만 정리하고 디렉토리 자체는 유지"""
    try:
        if not os.path.exists(html_dir):
            logging.warning(f"디렉토리가 존재하지 않음: {html_dir}")
            return

        # 디렉토리 내부의 모든 항목 삭제
        for item in os.listdir(html_dir):
            item_path = os.path.join(html_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

        logging.info(f"📦 HTML 디렉토리 내부 정리 완료: {html_dir}")
    except Exception as e:
        logging.error(f"❌ HTML 디렉토리 정리 실패: {e}")

with DAG(
    'news_pipeline_dag_test',
    default_args=default_args,
    description='뉴스 파이프라인 테스트',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=['rss', 'html', 'parser', 'news', 'embedding', 'test'],
) as dag:

    process_feeds_task = PythonOperator(
        task_id='process_feeds',
        python_callable=process_feeds_test,
    )
    
    upload_html_task = PythonOperator(
        task_id='upload_html_to_s3',
        python_callable=upload_html_to_s3,
        op_kwargs={
            'html_dir': os.environ["RSS_FEED_HTML_DIR"],
            'bucket_name': os.environ["AWS_S3_BUCKET"]
        }
    )

    index_articles_task = PythonOperator(
        task_id='index_articles',
        python_callable=index_articles,
    )

    cleanup_html_task = PythonOperator(
        task_id='cleanup_html',
        python_callable=cleanup_html,
        op_kwargs={
            'html_dir': os.environ["RSS_FEED_HTML_DIR"]
        }
    )

    # 태스크 의존성 설정
    process_feeds_task >> upload_html_task >> index_articles_task >> cleanup_html_task
    