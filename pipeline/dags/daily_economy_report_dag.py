# /dags/daily_economy_report_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta, datetime
import os
from logger import get_logger
from airflow.operators.bash import BashOperator
from airflow.sensors.time_delta import TimeDeltaSensor

# 태스크 임포트
from tasks.retrieve_news_task import retrieve_news
from tasks.check_sufficient_task import check_sufficient
from tasks.generate_card_reports_task import generate_card_reports
from tasks.format_to_markdown_task import format_to_markdown
from tasks.save_report_task import save_report
from tasks.send_to_slack_task import send_to_slack
from tasks.s3_upload_task import upload_to_s3
from tasks.convert_md_to_html_task import convert_md_to_html

logger = get_logger(__name__)

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 메모리 집약적 태스크를 위한 executor 설정
high_memory_config = {
    "pool": "high_memory_pool",
    "queue": "high_memory_queue"
}

# S3 버킷 이름 가져오기
def get_archive_bucket():
    return os.environ.get('ARCHIVE_BUCKET', 'economy-report-archive')

def get_report_bucket():
    return os.environ.get('REPORT_BUCKET', 'economy-report')

# GitHub Pages URL 가져오기
def get_my_page_url():
    return os.environ.get('MY_PAGE_URL', 'https://economy-report.eeddyy.org/')

# 예시: "2025/04/28.md" 형태
def get_object_key():
    now = datetime.now()
    return f"{now.year}/{now.month:02}/{now.day:02}.md"

with DAG(
    dag_id='daily_economy_report_dag',
    default_args=default_args,
    start_date=days_ago(1), 
    schedule_interval="0 0 * * *",  # UTC 0시 (KST 9시)
    catchup=False,
    tags=['news', 'report'],
) as dag:
    
    # 1. 뉴스 검색 및 가져오기
    retrieve_news_task = PythonOperator(
        task_id='retrieve_news',
        python_callable=retrieve_news,
        op_kwargs={
            'temp_file_path': '/tmp/retrieved_articles.json'
        },
    )
    
    # 2. 충분성 체크 (메모리 많이 사용)
    check_sufficient_task = PythonOperator(
        task_id='check_sufficient',
        python_callable=check_sufficient,
        op_kwargs={
            'input_file_path': '/tmp/retrieved_articles.json',
        },
        executor_config=high_memory_config,
    )
    
    # 3. 카드 리포트 생성 (메모리 많이 사용)
    generate_card_reports_task = PythonOperator(
        task_id='generate_card_reports',
        python_callable=generate_card_reports,
        op_kwargs={
            'output_file_path': '/tmp/card_reports.json',
            'max_reports': 5
        },
        executor_config=high_memory_config,
    )
    
    # 4. 마크다운으로 포맷팅
    format_to_markdown_task = PythonOperator(
        task_id='format_to_markdown',
        python_callable=format_to_markdown,
        op_kwargs={
            'input_file_path': '/tmp/card_reports.json',
            'output_file_path': '/tmp/markdown_report.md'
        },
    )
    
    # 5. 리포트 저장
    save_report_task = PythonOperator(
        task_id='save_report',
        python_callable=save_report,
        op_kwargs={
            'input_file_path': '/tmp/markdown_report.md',
            'output_file_path': '/tmp/daily_economy_report.md'
        },
    )
    
    # 6. S3에 마크다운 업로드 (Archive용)
    s3_upload_task_archive = PythonOperator(
        task_id='s3_upload_archive',
        python_callable=upload_to_s3,
        op_kwargs={
            'file_path': '/tmp/daily_economy_report.md',
            'bucket_name': get_archive_bucket(),
            'object_key': get_object_key(),
            'content_type': 'text/markdown',
            'public_read': False
        },
    )
    
    # 7. 마크다운을 HTML로 변환
    convert_md_to_html_task = PythonOperator(
        task_id='convert_md_to_html',
        python_callable=convert_md_to_html,
        op_kwargs={
            'md_file_path': '/tmp/daily_economy_report.md',
            'html_file_path': '/tmp/index.html'
        },
    )
    
    # 8. S3에 HTML 업로드 (Report용)
    s3_upload_task_report = PythonOperator(
        task_id='s3_upload_report',
        python_callable=upload_to_s3,
        op_kwargs={
            'file_path': '/tmp/index.html',
            'bucket_name': get_report_bucket(),
            'object_key': 'index.html',
            'content_type': 'text/html',
            'public_read': False
        },
    )
    
    # 10분 대기
    wait_task = TimeDeltaSensor(
        task_id='wait_10_minutes',
        delta=timedelta(minutes=10),
        poke_interval=60,  # 1분마다 확인
    )
    
    # 9. 슬랙으로 전송 (10분 후)
    send_to_slack_task = PythonOperator(
        task_id='send_to_slack',
        python_callable=send_to_slack,
        op_kwargs={
            'card_reports_path': '/tmp/card_reports.json',
            'report_url': get_my_page_url(),
        },
    )
    
    # 워크플로우 정의
    retrieve_news_task >> check_sufficient_task >> generate_card_reports_task >> format_to_markdown_task >> save_report_task
    save_report_task >> s3_upload_task_archive >> convert_md_to_html_task >> s3_upload_task_report >> wait_task >> send_to_slack_task
