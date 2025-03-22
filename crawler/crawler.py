import os
import boto3
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
import json
import random
from typing import Optional, List
import requests
from urllib.parse import urlparse
import io
import gc
import sys
from enum import Enum

# 환경변수에서 로그 레벨 설정 (기본은 INFO)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger(__name__)

# 환경변수로부터 SQS 큐 URL 받아오기
FAILURE_QUEUE_URL: str = os.environ.get("FAILURE_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/859805987151/MyTestDLQ")
RESUME_DATE_STR: Optional[str] = os.environ.get("RESUME_DATE")  # 예: "2025-02-15"
CATEGORY = os.environ.get("CATEGORY", "unknown")
TARGET_URL = os.environ.get("TARGET_URL")
XPATH_CHANGE_DATE = os.environ.get("XPATH_CHANGE_DATE")
URL_STORAGE_BUCKET = "article-crawl-html-storage"

class ErrorType(Enum):
    RETRY_ONCE = "RETRY_ONCE"
    RETRY_ALL = "RETRY_ALL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    S3 = "S3"
    HTML = "HTML"

# SQS 클라이언트 생성 (리전 명시)
sqs_client = boto3.client('sqs', region_name='ap-northeast-2')

# S3 클라이언트 생성
s3_client = boto3.client('s3', region_name='ap-northeast-2')

# === 공통 CSS 셀렉터 및 URL 제외 설정 ===
CSS_PAGING_SELECTOR = "div#paging a.paging-num"
XPATH_PAGING_BUTTON_TEMPLATE = "//div[@id='paging']/a[text()='{page_number}']"
CSS_ARTICLE_LIST = "#recentList li"
CSS_ARTICLE_TITLE = "h2.tit a"
CSS_ARTICLE_BYLINE = ".byline"
CSS_ARTICLE_SUMMARY = ".lead"
EXCLUDE_URLS = [
    '/login', '/SecListData.html',
    '/national/national-general/article/201709021732001',
    '/national/national-general/article/201609241422011',
    '/article/201709021732001'
]

def send_failure_message(error_type: str, error: Exception, resume_date: str = None):
    message = {
        "category": CATEGORY,
        "error_type": error_type,
        "error": str(error),
        "resume_date": resume_date
    }
    sqs_client.send_message(QueueUrl=FAILURE_QUEUE_URL, MessageBody=json.dumps(message))
    logger.error(f"[{CATEGORY}] 실패 큐에 전송 | Type: {error_type} | Resume: {message['resume_date']}")

# === 드라이버 및 딜레이 설정 함수 ===
def get_chrome_options() -> Options:
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    return options

def init_driver() -> webdriver.Chrome:
    try:
        driver = webdriver.Chrome(options=get_chrome_options())
        logger.info(f"[{CATEGORY}] 드라이버 초기화 성공")
        return driver
    except Exception as e:
        send_failure_message(ErrorType.NEEDS_REVIEW, e)
        raise

def polite_delay(min_delay: float = 1.0, max_delay: float = 3.0) -> None:
    delay = random.uniform(min_delay, max_delay)
    logger.debug(f"잠시 대기: {delay:.2f}초")
    time.sleep(delay)

# === 날짜 변경 함수 (오류 발생 시 FailureQueue에 로그 전송) ===
def change_date(driver: webdriver.Chrome, target_date: datetime, xpath: str) -> bool:
    try:
        btn = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception as e:
        logger.error(f"[{CATEGORY}] 날짜 변경 실패 | {target_date.strftime('%Y-%m-%d')} | Error: {str(e)}")
        logger.error("태스크를 종료합니다.")
        send_failure_message(ErrorType.NEEDS_REVIEW, "f{CATEGORY}-{target_date.strftime('%Y-%m-%d')} 날짜 변경 실패, 크롤링 종료.", target_date.strftime('%Y-%m-%d'))
        sys.exit(0)
        return False

# === 페이징 및 기사 추출 함수 (오류 발생 시 FailureQueue에 로그 전송) ===
def extract_articles_from_page(driver: webdriver.Chrome, wait: WebDriverWait, current_date) -> List[str]:
    try:
        # 기사 리스트 컨테이너가 로드될 때까지 대기
        container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#recentList")))
        articles = container.find_elements(By.CSS_SELECTOR, "li")  # 실제 기사 요소 조회
        
        # 기사가 없는 경우 빈 리스트 반환 (정상 처리)
        if not articles:
            logger.info(f"[{CATEGORY}]-{current_date} 기사 0건 - 정상 처리")
            
        return [article.find_element(By.CSS_SELECTOR, CSS_ARTICLE_TITLE).get_attribute("href") for article in articles]

    except Exception as e:
        # 실제 예외 발생시에만 에러 로깅
        logger.error(f"[{CATEGORY}]-{current_date} 기사 추출 실패 | Error: {str(e)}", exc_info=True)
        send_failure_message(ErrorType.RETRY_ONCE, e, resume_date=current_date)
        return []

def get_total_pages(driver: webdriver.Chrome) -> int:
    try:
        paging_links = driver.find_elements(By.CSS_SELECTOR, CSS_PAGING_SELECTOR)
        if not paging_links:  # 페이지 요소가 없는 경우 단일 페이지로 간주
            logger.info("페이지네이션 요소 없음, 단일 페이지 처리")
            return 1
        max_page = max([int(link.text) for link in paging_links if link.text.isdigit()])
        logger.info(f"현재 최대 페이지: {max_page}")
        return max_page
    except Exception as e:
        logger.warning(f"페이지 정보를 가져올 수 없어 단일 페이지 처리: {str(e)}")
        return 1  # 예외 발생 시 기본값 1 반환

def go_to_page(driver: webdriver.Chrome, wait: WebDriverWait, page: int) -> bool:
    try:
        xpath = XPATH_PAGING_BUTTON_TEMPLATE.format(page_number=page)
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception as e:
        logger.error(f"[{CATEGORY}] 페이지 이동 실패 | 목표 페이지: {page} | Error: {str(e)}")
        return False

def simple_download_html(link: str, target_date: str) -> None:
    """개선된 requests 다운로드 (메모리 최적화 및 S3 연동)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        time.sleep(random.uniform(1, 2))
        parsed_url = urlparse(link)
        path_parts = parsed_url.path.split('/')
        article_number = path_parts[-1]
        filename = f"{article_number}.html"

        with requests.Session() as session:
            session.headers.update(headers)
            
            # 스트리밍 다운로드로 메모리 사용량 최적화
            with session.get(link, stream=True, timeout=10) as response:
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code} 응답"
                    logger.error(f"응답 실패: {response.status_code}")
                    send_failure_message(ErrorType.S3, Exception(error_msg), target_date)
                    return

                # 청크 단위 쓰기로 메모리 부하 감소
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                logger.info(f"임시 파일 저장 완료: {filename}")
                
                # 파일에서 직접 읽어 S3 업로드
                with open(filename, 'rb') as f:
                    html_content = f.read()
                    upload_to_s3(html_content, link, file_name=filename)
                
                # 업로드 성공 후 즉시 파일 삭제
                os.remove(filename)
                logger.info(f"S3 업로드 후 파일 삭제: {filename}")

                # 명시적 메모리 해제
                del html_content
                gc.collect()

    except Exception as e:
        logger.error(f"다운로드 실패 | URL: {link} | 날짜: {target_date} | Error: {str(e)}", exc_info=True)
        send_failure_message("HTML_DOWNLOAD", e, target_date)
    finally:
        # 예외 발생 시에도 파일 정리
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)
            logger.warning(f"예외 발생으로 인한 파일 정리: {filename}")

def upload_to_s3(html_content: bytes, url: str, file_name) -> bool:  # 반환 타입 추가
    try:
        s3_key = f"{CATEGORY}/{file_name}"

        # 메모리 효율성을 위한 스트리밍 업로드
        with io.BytesIO(html_content) as buffer:
            s3_client.upload_fileobj(
                Fileobj=buffer,
                Bucket=URL_STORAGE_BUCKET,
                Key=s3_key,
                ExtraArgs={'ContentType': 'text/html'}
            )
        logger.info(f"S3 업로드 성공 | Key: {s3_key}")
        return True  # 성공 여부 반환
    except Exception as e:
        logger.error(f"S3 업로드 실패 | URL: {url} | Error: {str(e)}")
        send_failure_message(ErrorType.S3, e)
        return False  # 실패 시 False 반환

def format_date(dt: datetime, include_time: bool = False) -> str:
    """datetime을 문자열로 간단 포맷팅"""
    return dt.strftime('%Y-%m-%d %H:%M:%S') if include_time else dt.strftime('%Y-%m-%d')

# === 카테고리 크롤링 메인 함수 ===
def crawl_category(config: dict) -> None:
    category = config.get('category', 'unknown')
    
    # 종료 날짜를 간단한 날짜로 설정
    END_DATE = datetime(2020, 1, 1)
    
    # 타겟 날짜 초기화 (어제 날짜 기준)
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        
    logger.info(f"🚀 [{category}] 크롤링 시작 | 범위: {format_date(base_date)} ~ {format_date(END_DATE)}")

    driver = init_driver()
    wait = WebDriverWait(driver, 10)
    
    try:
        driver.get(config["url"])
        logger.info(f"[{category}] URL 로드 완료")
    except Exception as e:
        logger.error(f"[{category}] URL 로드 실패 | Error: {str(e)}")
        driver.quit()
        return
    
    target_date = base_date

    if config.get('resume_date') != None and config.get('resume_date') != target_date:
        try:
            resume_date = config.get('resume_date')
            logger.info(f"{target_date}를 {resume_date}까지 이동합니다.")
            while target_date != resume_date:
                logger.info(f"현재날짜: {target_date}, 타겟날짜: {resume_date}.")
                change_date(driver, resume_date, config["xpath_change_date"])
                target_date -= timedelta(days=1)
                polite_delay(0.5, 1)
        except Exception as e:
            send_failure_message("FAIL_AGAIN", e)
            logger.error(f"[{category}] 이동 실패 | Error: {str(e)}")
            driver.quit()
    
        logger.info("f{target_date}로 이동 완료. 크롤링을 진행합니다.")
    while target_date >= END_DATE:
        current_date_str = format_date(target_date)
        logger.info(f"[{category}] 현재 처리 날짜: {current_date_str}")
        
        # 3. 날짜 변경 시도 (다음 버튼 클릭)
        if not change_date(driver, target_date, config["xpath_change_date"]):
            logger.warning(f"[{category}] 날짜 변경 실패 | 건너뜀")
            target_date -= timedelta(days=1)
            continue

        # 페이지네이션 처리 (기존 코드 유지)
        current_page = 1
        while True:
            total_pages = get_total_pages(driver)
            target_date_str = format_date(target_date)
            logger.info(f"[{category}][{target_date_str}] 페이지 진행 | {current_page}/{total_pages}")
            
            # 기사 추출
            articles = extract_articles_from_page(driver, wait, target_date)
            
            if articles:
                for article in articles:
                    simple_download_html(article, target_date_str)
                logger.info(f"[{category}][{target_date_str}] {len(articles)}개 기사 처리 완료")
            else:
                logger.warning(f"[{category}][{target_date_str}] {target_date_str} 기사 없음")

            if current_page >= total_pages:
                logger.info(f"[{category}][{target_date_str}] 마지막 페이지 도달")
                break
                
            if not go_to_page(driver, wait, current_page + 1):
                logger.warning(f"[{category}][{target_date_str}] 페이지 이동 실패. 크롤링 중단")
                break
                
            current_page += 1
            polite_delay(2, 3)

        # 4. 날짜 갱신 (루프 종료 조건 확인)
        target_date -= timedelta(days=1)
        if target_date < END_DATE:
            logger.info(f"[{category}] {format_date(END_DATE)} 도달. 크롤링 종료")
            break

    logger.info(f"[{category}] 크롤링 완료")
    driver.quit()

def main() -> None:
    resume_date: Optional[datetime] = None
    if RESUME_DATE_STR:
        try:
            resume_date = datetime.strptime(RESUME_DATE_STR, "%Y-%m-%d")
        except Exception as e:
            logger.error(f"RESUME_DATE 형식 오류: {e}")
    config = {
        "category": CATEGORY,
        "url": TARGET_URL,
        "xpath_change_date": XPATH_CHANGE_DATE,
        "resume_date": resume_date
    }
    crawl_category(config)

if __name__ == '__main__':
    if not all([TARGET_URL, XPATH_CHANGE_DATE]):  # URL_TASK_QUEUE_URL 검증 제거
        logger.error("필수 환경변수가 설정되지 않았습니다")
        exit(1)
        
    main()
    logger.info(f"=== [{CATEGORY}] 크롤링 종료 ===")
