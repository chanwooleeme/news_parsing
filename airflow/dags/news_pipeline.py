from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

from tasks.download_html_task import download_html_task
from tasks.parse_articles_task import parse_and_save_articles_task
from tasks.embed_and_search_task import embed_and_search_task
from tasks.analyze_article_task import analyze_article_task
from tasks.save_analysis_task import save_analysis_task

# 경로 세팅 (환경변수 읽거나, 직접 지정)
HTML_DIR = os.getenv("HTML_FILES_DIR", "/opt/airflow/data/html_files")
PARSED_DIR = os.getenv("PARSED_FILES_DIR", "/opt/airflow/data/parsed_articles")
ANALYSIS_DIR = os.getenv("ANALYSIS_FILES_DIR", "/opt/airflow/data/analysis_results")
RSS_SOURCE_FILE = os.getenv("RSS_SOURCE_FILE", "/opt/airflow/data/news_file.json")
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='news_pipeline_dag',
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval='@hourly',  # 1시간마다
    catchup=False,
    tags=['news', 'pipeline']
) as dag:

    @task
    def download_html():
        download_html_task(
            html_download_dir=HTML_DIR,
            rss_source_file=RSS_SOURCE_FILE
        )

    @task
    def parse_articles():
        parse_and_save_articles_task(
            html_base_dir=HTML_DIR,
            parsed_base_dir=PARSED_DIR
        )

    @task
    def embed_and_search():
        return embed_and_search_task(
            parsed_base_dir=PARSED_DIR,
            top_k=5
        )

    @task
    def analyze_articles(results: list):
        return analyze_article_task(
            results=results
        )

    @task
    def save_analysis(analyzed_results: list):
        save_analysis_task(
            analyzed_results=analyzed_results,
            save_base_dir=ANALYSIS_DIR
        )

    # 👉 DAG Task Dependency
    download = download_html()
    parsed = parse_articles()
    embedded = embed_and_search()
    analyzed = analyze_articles(embedded)
    saved = save_analysis(analyzed)

    download >> parsed >> embedded >> analyzed >> saved
