from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowSkipException
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

from tasks.download_html_task import download_html_task
from tasks.parse_filtered_articles_task import parse_and_save_articles_task
from tasks.s3_upload_task import s3_upload_task
from tasks.predict_economy_articles_task import predict_economy_articles_task


# 경로 세팅 (환경변수 읽거나, 직접 지정)
BASE_DATA_DIR = os.getenv("BASE_DATA_DIR", "/opt/airflow/data")
HTML_DIR = os.path.join(BASE_DATA_DIR, "html_files")
PARSED_DIR = os.path.join(BASE_DATA_DIR, "parsed_articles")
RSS_SOURCE_FILE = os.getenv("RSS_SOURCE_FILE", "/opt/airflow/data/economy.json")
PICKLE_PATH = os.getenv("PICKLE_PATH", "/opt/airflow/data/minhash_lsh.pkl")

# 각 실행별 고유 경로 생성 함수
def get_run_specific_path(base_dir, run_id):
    """각 DAG 실행별 고유 경로 생성"""
    return os.path.join(base_dir, f"run_{run_id}")

# 메모리 집약적 태스크를 위한 설정
high_memory_config = {
    "pool": "high_memory_pool",
    "queue": "high_memory_queue"
}

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
    tags=['news', 'pipeline'],
) as dag:

    @task
    def download(**context):
        # 실행별 고유 디렉토리 사용
        run_id = context['run_id'] 
        html_run_dir = get_run_specific_path(HTML_DIR, run_id)
        
        download_result = download_html_task(
            html_download_dir=html_run_dir,
            rss_source_file=RSS_SOURCE_FILE,
        )
        if len(download_result) == 0:
            raise AirflowSkipException("새로운 기사 없음! 패스")

        return html_run_dir

    @task(executor_config=high_memory_config)
    def parse(html_dir, **context):
        # 실행별 고유 디렉토리 사용
        run_id = context['run_id']
        parsed_run_dir = get_run_specific_path(PARSED_DIR, run_id)
        
        parse_and_save_articles_task(   
            html_base_dir=html_dir,
            parsed_base_dir=parsed_run_dir,
            pickle_path=PICKLE_PATH
        )
        
        # 다음 태스크에서 사용할 수 있도록 경로 반환
        return parsed_run_dir

    @task(executor_config=high_memory_config)
    def predict(parsed_dir):
        # 기사 예측 async 호출
        predict_economy_articles_task(parsed_dir=parsed_dir)

    @task
    def upload_to_s3(html_dir):
        s3_upload_task(html_dir=html_dir)
        return html_dir

    # @task
    # def delete_file(html_dir, parsed_dir):
    #     delete_file_task(html_dir=html_dir, parsed_news_dir=parsed_dir)

    # 태스크 호출 및 의존성 설정
    html_dir = download()
    parsed_dir = parse(html_dir)
    predict_result = predict(parsed_dir)
    upload_result = upload_to_s3(html_dir)
    # delete_result = delete_file(html_dir=html_dir, parsed_dir=parsed_dir)
    
    # 태스크 간 의존성 설정
    html_dir >> parsed_dir >> predict_result

    # 2. upload는 download 후 언제든 가능
    html_dir >> upload_result

    # 3. delete는 모든 작업이 완료된 후에만 실행
    # [upload_result, embed_result] >> delete_result