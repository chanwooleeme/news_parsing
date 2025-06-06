"""
Airflow 태스크 모듈

뉴스 파이프라인 DAG에서 사용되는 태스크를 제공합니다.
"""

# 모든 태스크를 직접 import하지 않고, 필요할 때마다 개별적으로 import하여 사용하세요.
# 이렇게 하면 태스크 간의 불필요한 의존성을 방지할 수 있습니다. 