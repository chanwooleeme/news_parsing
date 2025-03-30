#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import os
import glob
import logging
from typing import Dict, List, Any
import json
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.redis.hooks.redis import RedisHook

# RSS 피드 모듈 가져오기
from rss_feed.feed_parser import FeedParser

# HTML 파서 모듈 가져오기
from html_parser.parser_factory import ParserFactory

# 임베딩 처리 모듈 가져오기
from indexer.batch_embedder import (
    create_embedding_jsonl,
    upload_and_create_batch,
    check_batch_status,
    download_and_process_results
)

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

def process_html_files(**kwargs):
    """HTML 파일을 파싱하여 기사 정보를 추출하고 결과를 S3에 저장합니다."""
    
    # HTML 디렉토리 경로
    html_dir = os.environ.get('RSS_FEED_HTML_DIR', '/opt/airflow/data/html')
    logging.info(f"HTML 디렉토리: {html_dir}")
    
    # S3 설정
    s3_hook = S3Hook(aws_conn_id='aws_default')
    bucket_name = os.environ.get('AWS_S3_BUCKET')
    
    # 파서 팩토리 초기화
    factory = ParserFactory()
    supported_newspapers = factory.get_supported_newspapers()
    logging.info(f"지원되는 신문사: {supported_newspapers}")
    
    # 결과 저장 리스트
    parsed_results = []
    
    # 처리된 HTML 파일 수 카운터
    processed_count = 0
    success_count = 0
    
    # html 디렉토리 내의 모든 .html 파일 처리
    for html_file in glob.glob(os.path.join(html_dir, '**', '*.html'), recursive=True):
        try:
            # 파일 경로에서 신문사 이름 추출
            # 예: /opt/airflow/data/html/조선일보/article123.html -> 조선일보
            relative_path = os.path.relpath(html_file, html_dir)
            newspaper = relative_path.split(os.sep)[0]
            
            # 제외할 신문사 확인
            if newspaper in EXCLUDED_NEWSPAPERS:
                logging.info(f"제외된 신문사 {newspaper}의 파일 건너뜀: {html_file}")
                continue
                
            # 지원하지 않는 신문사 확인
            if newspaper not in supported_newspapers:
                logging.warning(f"지원하지 않는 신문사 {newspaper}의 파일 건너뜀: {html_file}")
                continue
            
            # HTML 파일 읽기
            with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()
            
            # 파싱 실행
            result = factory.parse(html_content, newspaper)
            
            # S3에 파싱 결과 저장
            s3_key = f"parsed_articles/{newspaper}/{os.path.basename(html_file).replace('.html', '.json')}"
            s3_hook.load_string(
                json.dumps(result, ensure_ascii=False),
                s3_key,
                bucket_name=bucket_name,
                replace=True
            )
            
            logging.info(f"성공적으로 파싱 및 저장: {s3_key}")
            
            # 파싱 결과 요약 저장
            parsed_results.append({
                'newspaper': newspaper,
                'title': result.get('title', '')[:50] + ('...' if len(result.get('title', '')) > 50 else ''),
                'author': result.get('author', ''),
                'content_length': len(result.get('content', '')),
                'file_path': html_file,
                's3_key': s3_key
            })
            
            success_count += 1
                
        except Exception as e:
            logging.error(f"파일 처리 중 오류 발생: {html_file}, 오류: {str(e)}")
        
        processed_count += 1
    
    logging.info(f"HTML 파싱 완료: 총 {processed_count}개 파일 중 {success_count}개 성공")
    return {
        'processed_count': processed_count,
        'success_count': success_count,
        'parsed_results': parsed_results[:10]  # 처음 10개 결과만 반환
    }

# 배치 작업 완료 여부 확인 함수
def is_batch_completed(**kwargs):
    """
    배치 작업이 완료되었는지 확인하는 센서 함수
    완료된 경우 True를 반환하여 다음 작업으로 진행
    """
    ti = kwargs['ti']
    batch_status = ti.xcom_pull(task_ids='check_batch_status')
    
    if not batch_status:
        return False
    
    status = batch_status.get('status')
    
    # 배치 작업이 완료된 경우
    if status == 'completed':
        return True
    
    # 배치 작업이 실패한 경우 (다음 작업으로 진행하지 않음)
    if status in ['failed', 'cancelled', 'expired']:
        raise ValueError(f"배치 작업이 실패했습니다: {status}")
    
    # 아직 진행 중인 경우
    return False

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
    
    # HTML 파일 파싱 및 결과 저장
    parse_html_files_task = PythonOperator(
        task_id='parse_html_files_task',
        python_callable=process_html_files,
        provide_context=True,
    )
    
    # HTML 파일 파싱 및 JSONL 생성 (임베딩용)
    create_jsonl = PythonOperator(
        task_id='create_embedding_jsonl',
        python_callable=create_embedding_jsonl,
        provide_context=True,
    )
    
    # JSONL 파일 업로드 및 배치 작업 생성
    create_batch = PythonOperator(
        task_id='upload_and_create_batch',
        python_callable=upload_and_create_batch,
        provide_context=True,
    )
    
    # 배치 상태 확인
    check_status = PythonOperator(
        task_id='check_batch_status',
        python_callable=check_batch_status,
        provide_context=True,
    )
    
    # 배치 작업 완료 대기
    wait_for_batch = PythonSensor(
        task_id='wait_for_batch_completion',
        python_callable=is_batch_completed,
        timeout=24 * 60 * 60,  # 최대 24시간 대기
        mode='reschedule',  # 다른 작업에 슬롯 양보
        poke_interval=600,  # 10분마다 확인
        provide_context=True,
    )
    
    # 결과 다운로드 및 처리
    process_results = PythonOperator(
        task_id='download_and_process_results',
        python_callable=download_and_process_results,
        provide_context=True,
    )
    
    # 태스크 의존성 설정
    # RSS 피드 처리 -> HTML 파싱 -> 임베딩 JSONL 생성 -> 배치 작업 생성 -> 상태 확인 -> 완료 대기 -> 결과 처리
    process_feeds_task >> parse_html_files_task >> create_jsonl >> create_batch >> check_status >> wait_for_batch >> process_results 