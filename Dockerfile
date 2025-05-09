FROM apache/airflow:2.7.3

USER root

# 필요 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# 코드 복사
COPY src /opt/airflow/src
COPY pyproject.toml /opt/airflow/pyproject.toml
COPY logger.py /opt/airflow/logger.py

# setup.py 생성
RUN echo 'from setuptools import setup; setup()' > /opt/airflow/setup.py

# PYTHONPATH 설정
ENV PYTHONPATH=/opt/airflow:$PYTHONPATH

# 로그 디렉토리 구조 생성
RUN mkdir -p /opt/airflow/logs/scheduler \
             /opt/airflow/logs/webserver \
             /opt/airflow/logs/worker \
             /opt/airflow/logs/dag_processor_manager \
             /opt/airflow/logs/tasks \
             /opt/airflow/logs/application

# 퍼미션 변경
RUN chown -R airflow:root /opt/airflow/src /opt/airflow/pyproject.toml /opt/airflow/setup.py /opt/airflow/logger.py /opt/airflow/logs /opt/airflow/airflow_logging.conf && \
    chmod -R 755 /opt/airflow/logs

# 볼륨 데이터 디렉토리 세팅
RUN mkdir -p /opt/airflow/data /opt/airflow/plugins && \
    chmod -R 777 /opt/airflow/data /opt/airflow/plugins

RUN mkdir -p /opt/airflow/data/html_files /opt/airflow/data/parsed_articles /opt/airflow/data/analysis_results /opt/airflow/data/summarize_report && \
    chmod -R 777 /opt/airflow/data

# airflow 유저로
USER airflow

RUN pip install openai qdrant-client tiktoken feedparser markdown datasketch redis

# 패키지 설치
RUN pip install -e /opt/airflow

# dags와 tasks, utils 디렉토리 생성 (볼륨 마운트용)
RUN mkdir -p /opt/airflow/dags /opt/airflow/tasks /opt/airflow/utils && \
    chmod -R 755 /opt/airflow/dags /opt/airflow/tasks /opt/airflow/utils
