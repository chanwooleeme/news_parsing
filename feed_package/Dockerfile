# [테스트] 도커환경에서 테스트
FROM python:3.8-slim

WORKDIR /app

# 시스템 패키지 설치 및 정리
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 패키지 파일 복사
COPY rss_feed_package /app/rss_feed_package
COPY MANIFEST.in /app/

# 환경 변수는 실행 시점에 주입할 수 있도록 기본값만 설정
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""
ENV AWS_REGION=""
ENV AWS_S3_BUCKET=""
ENV RSS_FEED_HTML_DIR=""

# 데이터 디렉터리 생성
RUN mkdir -p /app/data/html

# 패키지 설치
RUN pip install --no-cache-dir -e /app/rss_feed_package

# 테스트 스크립트 복사
COPY data /app/data


CMD ["bash"]