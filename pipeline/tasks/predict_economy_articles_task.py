from typing import List, Dict
from logging import getLogger
from utils.file import list_directories, list_files, join_path, read_json_file
import requests
import os

logger = getLogger(__name__)
MAX_BATCH_SIZE = 100
BASE_API_URL = os.getenv("BASE_API_URL")

# 📰 기사 로딩
def load_articles_from_directory(base_dir: str) -> List[Dict]:
    articles = []

    for newspaper in list_directories(base_dir):
        newspaper_dir = join_path(base_dir, newspaper)
        for filename in list_files(newspaper_dir, extension=".json"):
            json_path = join_path(newspaper_dir, filename)
            try:
                article = read_json_file(json_path)
                content = article.get("content", "")

                if not content:
                    logger.warning(f"❌ Content 비어있음: {json_path}")
                    continue
                elif len(content) <= 100:
                    logger.warning(f"❌ Content 길이 너무 짧은 기사: {json_path}")
                    continue

                articles.append(article)
            except Exception as e:
                logger.error(f"❌ {newspaper}/{filename} 읽기 실패: {e}")
    
    logger.info(f"총 {len(articles)}개 기사 수집 완료")
    return articles

# 🧩 배치 나누기
def batch_articles(articles: List[Dict], batch_size: int = MAX_BATCH_SIZE) -> List[Dict]:
    return [
        {"articles": articles[i:i + batch_size]}
        for i in range(0, len(articles), batch_size)
    ]


# 🚀 동기 API 호출 (수정)
def call_predict(batch, idx): # async 제거, session 제거
    try:
        # aiohttp 대신 requests 사용 (수정)s
        response = requests.post(BASE_API_URL + "/predict", json=batch, timeout=180) # 타임아웃 3분으로 설정
        logger.info(f"✅ Batch {idx} 응답 코드: {response.status_code}") # resp.status -> response.status_code
        # 응답 상태 코드 확인 추가
        if response.status_code != 200:
             logger.error(f"❌ Batch {idx} 처리 실패: Status {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e: # aiohttp 예외 대신 requests 예외 처리 (수정)
        logger.error(f"❌ Batch {idx} 요청 실패: {e}")
    except Exception as e: # 일반 예외 처리 추가
        logger.error(f"❌ Batch {idx} 처리 중 예상치 못한 오류: {e}")


def predict_all_batches(batches): # async 제거 (수정)
    # asyncio.gather 대신 단순 for 루프 사용 (수정)
    for idx, batch in enumerate(batches):
        call_predict(batch, idx + 1) 

# 🎯 최종 실행 함수
def predict_economy_articles_task(parsed_dir: str):
    logger.info("API URL: " + BASE_API_URL + "/predict")
    articles = load_articles_from_directory(parsed_dir)
    batches = batch_articles(articles)

    logger.info(f"🚀 총 {len(batches)}개 배치 동기 요청 시작")      
    predict_all_batches(batches)
    logger.info("✅ 모든 기사 예측 완료")
