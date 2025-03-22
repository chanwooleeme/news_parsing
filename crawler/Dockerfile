# Selenium의 공식 Standalone Chrome 이미지를 베이스로 사용
FROM selenium/standalone-chrome:latest

# root 권한으로 변경
USER root

# Python3 및 pip 설치
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 생성
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# 애플리케이션 코드 복사
COPY . /app/

# 컨테이너 시작 시 실행할 명령어 (실제 메인 스크립트 이름으로 변경)
CMD ["python3", "crawler.py"]
