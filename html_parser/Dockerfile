# Python 3.9-slim 이미지를 베이스로 사용합니다.
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 빌드 및 실행에 필요한 패키지 설치 (BeautifulSoup 파싱 성능 향상을 위해 libxml2, libxslt 설치)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 컨테이너 실행 시 기본 명령 (필요 시 환경변수는 docker run 명령에서 지정)
CMD ["python", "parser.py"]
