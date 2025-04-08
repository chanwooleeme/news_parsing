FROM apache/airflow:2.7.3

USER root

# 필요 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# 코드 복사
COPY src /opt/airflow/src
COPY pyproject.toml /opt/airflow/pyproject.toml

# setup.py 생성
RUN echo 'from setuptools import setup; setup()' > /opt/airflow/setup.py

# 퍼미션 변경
RUN chown -R airflow:root /opt/airflow/src /opt/airflow/pyproject.toml /opt/airflow/setup.py

# 볼륨 데이터 디렉토리 세팅
RUN mkdir -p /opt/airflow/data /opt/airflow/logs /opt/airflow/plugins && \
    chmod -R 777 /opt/airflow/data /opt/airflow/logs /opt/airflow/plugins

# airflow 유저로
USER airflow

# 추가 의존성 설치
RUN pip install apache-airflow-providers-celery psycopg2-binary redis

# 패키지 설치
RUN pip install -e /opt/airflow

# dags와 tasks, utils 복사
COPY pipeline/dags /opt/airflow/dags
COPY pipeline/tasks /opt/airflow/tasks
COPY pipeline/utils /opt/airflow/utils
