# RSS Feed Parser

RSS 피드를 파싱하고, 기사 내용을 다운로드하며, S3에 저장하는 패키지입니다.

## 특징

- RSS 피드에서 기사 링크 수집
- HTML 내용 다운로드 및 로컬 저장
- S3에 HTML 파일 업로드
- Redis를 사용한 중복 처리 방지

## 설치

```bash
pip install -e .
```

## 사용법

### 기본 사용법

```python
from rss_feed import create_default_parser

parser = create_default_parser()
parser.process_feeds()
```

### 빌더 패턴을 사용한 사용자 정의

```python
from rss_feed import FeedParserBuilder

parser = FeedParserBuilder()\
    .with_base_dir('/path/to/data')\
    .with_html_dir('/path/to/html')\
    .with_news_file_path('/path/to/news_file.json')\
    .with_redis_config('localhost', 6379, 'password')\
    .with_aws_config('ap-northeast-2', 'your-access-key', 'your-secret-key')\
    .with_s3_bucket('your-bucket-name')\
    .build()

parser.process_feeds()
```

### 환경 변수 설정

```bash
export RSS_FEED_BASE_DIR=/path/to/data
export RSS_FEED_HTML_DIR=/path/to/html
export RSS_FEED_NEWS_FILE=/path/to/news_file.json
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=password
export AWS_REGION=ap-northeast-2
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export S3_BUCKET_NAME=your-bucket-name
```

## 라이센스

MIT 