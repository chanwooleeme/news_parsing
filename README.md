# 뉴스 파싱 및 경제 리포트 생성 파이프라인

## 프로젝트 개요
이 프로젝트는 뉴스 기사를 수집, 분석하여 경제 리포트를 자동으로 생성하는 Airflow 기반 파이프라인입니다.

## 시스템 요구사항
- Docker
- Docker Compose
- Python 3.8+

## 파이프라인 구조
```
news_pipeline_dag
├── download: 뉴스 기사 HTML 다운로드
├── parse: 기사 파싱 및 중복 제거
├── predict: 경제 관련 기사 분류
└── upload_to_s3: HTML 파일 S3 업로드

daily_economy_report_dag
├── retrieve_news: 최근 경제 뉴스 조회
├── check_sufficient: 충분한 기사 수 확인
├── generate_card_reports: 카드 리포트 생성
├── format_to_markdown: 마크다운 포맷 변환
├── save_report: 리포트 저장
├── convert_md_to_html: HTML 변환
├── upload_to_s3: S3 업로드
└── send_to_slack: 슬랙 알림 전송
```

## 시작하기

1. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일에 필요한 환경 변수 설정
```

2. 서비스 시작
```bash
docker compose up -d
```

3. Airflow 웹 인터페이스 접속
- URL: http://localhost:8080
- 기본 계정: admin/admin

## 주요 기능
- 뉴스 기사 자동 수집 및 파싱
- 중복 기사 제거 (MinHash + Redis)
- 경제 관련 기사 분류
- 일일 경제 리포트 자동 생성
- S3 저장 및 슬랙 알림

## 디렉토리 구조
```
.
├── pipeline/
│   ├── dags/          # Airflow DAG 파일
│   ├── tasks/         # 태스크 구현
│   └── utils/         # 유틸리티 함수
├── data/              # 데이터 저장
├── logs/              # 로그 파일
└── src/              # 소스 코드
``` 