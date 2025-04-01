FROM apache/airflow:2.7.3

USER root

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# RSS 피드 패키지 설치
COPY feed_package/rss_feed_package /opt/airflow/rss_feed_package
RUN chown -R airflow:root /opt/airflow/rss_feed_package

# HTML 파서 패키지 설치
COPY html_parser /opt/airflow/html_parser
RUN chown -R airflow:root /opt/airflow/html_parser

COPY indexer /opt/airflow/indexer
RUN chown -R airflow:root /opt/airflow/indexer


# 디렉토리 생성 및 권한 설정
RUN mkdir -p /opt/airflow/data/html /opt/airflow/data/jsonl /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins && \
    chmod -R 777 /opt/airflow/data /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins && \
    chown -R airflow:root /opt/airflow/data /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins

# 로그 디렉토리 생성 및 권한 설정
RUN mkdir -p /opt/airflow/logs/scheduler
RUN chmod -R 777 /opt/airflow/logs

USER airflow
# 패키지 설치
RUN pip install -e /opt/airflow/rss_feed_package
RUN pip install -e /opt/airflow/html_parser
RUN pip install -e /opt/airflow/indexer

# Airflow DAG 파일 복사
COPY airflow/dags /opt/airflow/dags

# 권한 재설정
USER root
RUN chown -R airflow:root /opt/airflow/dags
USER airflow

# 환경변수는 docker-compose.yml에서 처리합니다
