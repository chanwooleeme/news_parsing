# /dags/daily_economy_report_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
from datetime import timedelta
import os
from logger import get_logger

# 태스크 임포트
from tasks.retrieve_news_task import retrieve_news
from tasks.check_sufficient_task import check_sufficient
from tasks.generate_card_reports_task import generate_card_reports
from tasks.format_to_markdown_task import format_to_markdown
from tasks.save_report_task import save_report
from tasks.send_to_slack_task import send_to_slack

logger = get_logger(__name__)

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

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
    
    # 2. 충분성 체크
    check_sufficient_task = PythonOperator(
        task_id='check_sufficient',
        python_callable=check_sufficient,
        op_kwargs={
            'input_file_path': '/tmp/retrieved_articles.json',
            'output_file_path': '/tmp/sufficient_articles.json'
        },
    )
    
    # 3. 카드 리포트 생성
    generate_card_reports_task = PythonOperator(
        task_id='generate_card_reports',
        python_callable=generate_card_reports,
        op_kwargs={
            'input_file_path': '/tmp/sufficient_articles.json',
            'output_file_path': '/tmp/card_reports.json',
            'max_reports': 5
        },
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
            'output_file_path': 'daily_economy_report.md'
        },
    )
    
    # 6. 슬랙으로 전송
    send_to_slack_task = PythonOperator(
        task_id='send_to_slack',
        python_callable=send_to_slack,
        op_kwargs={
            'card_reports_path': '/tmp/card_reports.json',
            'report_url': "https://tmp.com",
        },
    )
    
    # 워크플로우 정의
    retrieve_news_task >> check_sufficient_task >> generate_card_reports_task >> format_to_markdown_task >> save_report_task >> send_to_slack_task
