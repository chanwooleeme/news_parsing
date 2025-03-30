#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import os
import glob
import logging
import json
from pathlib import Path
from typing import Dict, List, Any

from airflow import DAG
from airflow.operators.python import PythonOperator

# HTML 파서 모듈 가져오기
from html_parser.parser_factory import ParserFactory

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def parse_html_to_json():
    """HTML 파일을 파싱하여 JSON 파일로 저장합니다."""
    # HTML 디렉토리 경로
    html_dir = os.environ.get('RSS_FEED_HTML_DIR', '/opt/airflow/data/html')
    logging.info(f"HTML 디렉토리: {html_dir}")
    
    # JSON 저장 디렉토리 경로
    json_dir = os.environ.get('PARSER_JSON_DIR', '/opt/airflow/data/json')
    logging.info(f"JSON 저장 디렉토리: {json_dir}")
    
    # JSON 디렉토리 생성
    os.makedirs(json_dir, exist_ok=True)
    
    # 파서 팩토리 초기화
    factory = ParserFactory()
    supported_newspapers = factory.get_supported_newspapers()
    logging.info(f"지원되는 신문사: {supported_newspapers}")
    
    # 결과 저장 리스트
    parsed_results = []
    
    # 처리된 HTML 파일 수 카운터
    total_count = 0
    success_count = 0
    
    # html 디렉토리 내의 모든 .html 파일 처리
    html_files = glob.glob(os.path.join(html_dir, '**', '*.html'), recursive=True)
    logging.info(f"총 {len(html_files)}개 HTML 파일을 찾았습니다.")
    
    for html_file in html_files:
        total_count += 1
        try:
            # 파일 경로에서 신문사 이름 추출
            # 예: /opt/airflow/data/html/조선일보/article123.html -> 조선일보
            relative_path = os.path.relpath(html_file, html_dir)
            parts = relative_path.split(os.sep)
            newspaper = parts[0]
            
            # 지원하지 않는 신문사 확인
            if newspaper not in supported_newspapers:
                logging.warning(f"지원하지 않는 신문사 {newspaper}의 파일 건너뜀: {html_file}")
                continue
            
            # HTML 파일 읽기
            with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()
            
            # 파싱 실행
            result = factory.parse(html_content, newspaper)
            
            # 파싱 결과 로깅
            logging.info(f"신문사: {newspaper}")
            logging.info(f"제목: {result.get('title', '')}")
            logging.info(f"작성자: {result.get('author', '')}")
            logging.info(f"발행일: {datetime.fromtimestamp(result.get('publication_date', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"본문 (처음 100자): {result.get('content', '')[:100]}...")
            
            # JSON 파일 경로 생성
            # 신문사별 디렉토리 구조 유지
            output_dir = os.path.join(json_dir, newspaper)
            os.makedirs(output_dir, exist_ok=True)
            
            # 원본 파일명에서 .html 확장자를 .json으로 변경
            filename = os.path.basename(html_file)
            json_filename = os.path.splitext(filename)[0] + '.json'
            json_path = os.path.join(output_dir, json_filename)
            
            # JSON 파일로 저장
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logging.info(f"JSON 파일 저장 완료: {json_path}")
            
            # 파싱 결과 요약 저장
            parsed_results.append({
                'newspaper': newspaper,
                'title': result.get('title', ''),
                'author': result.get('author', ''),
                'publication_date': result.get('publication_date', 0),
                'json_path': json_path
            })
            
            success_count += 1
                
        except Exception as e:
            logging.error(f"파일 처리 중 오류 발생: {html_file}, 오류: {str(e)}")
    
    logging.info(f"HTML 파싱 및 JSON 저장 완료: 총 {total_count}개 파일 중 {success_count}개 성공")
    
    # 통계 정보를 JSON 파일로 저장
    stats = {
        'total_count': total_count,
        'success_count': success_count,
        'processed_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'parsed_results': parsed_results
    }
    
    stats_path = os.path.join(json_dir, 'parsing_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    logging.info(f"파싱 통계 저장 완료: {stats_path}")
    
    return {
        'total_count': total_count,
        'success_count': success_count,
        'parsed_files': [r['json_path'] for r in parsed_results[:10]]  # 처음 10개 결과만 반환
    }

with DAG(
    'html_parser_json_export_dag',
    default_args=default_args,
    description='HTML 파일을 파싱하여 JSON으로 내보내는 DAG',
    schedule_interval=None,  # 수동 실행
    catchup=False,
    tags=['html', 'parser', 'json', 'export'],
) as dag:
    
    # HTML 파싱 및 JSON 저장 태스크
    parse_html_to_json_task = PythonOperator(
        task_id='parse_html_to_json',
        python_callable=parse_html_to_json,
    ) 