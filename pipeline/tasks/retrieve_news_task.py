from logger import get_logger
from utils.config import BASE_API_URL, call_api
from typing import List

logger = get_logger(__name__)

API_URL = BASE_API_URL + "/search-articles"
    
def retrieve_news_task() -> List[dict]:
    logger.info("📰 뉴스 데이터 조회 시작")
    logger.info("API URL: " + API_URL)
    response = call_api(API_URL)
    logger.info("API 응답: " + str(response))
    return response['results']
