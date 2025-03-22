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

USER airflow
RUN pip install -e /opt/airflow/rss_feed_package

# Airflow DAG 파일 복사
COPY airflow/dags /opt/airflow/dags

# 권한 설정
USER root
RUN chown -R airflow:root /opt/airflow/dags
USER airflow

# PYTHONPATH 설정
ENV PYTHONPATH=/opt/airflow