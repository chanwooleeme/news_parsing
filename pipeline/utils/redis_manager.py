# redis_manager.py

import time
import json
import redis
from typing import List, Dict
from utils.config import REDIS_SERVER, REDIS_SERVER_PORT, REDIS_SERVER_PASSWORD
from logger import get_logger

logger = get_logger(__name__)

redis_client = redis.Redis(
    host=REDIS_SERVER,
    port=REDIS_SERVER_PORT,
    password=REDIS_SERVER_PASSWORD,
    decode_responses=True  # 문자열 자동 디코딩
)

# ✅ 2. 중요도별 기사 Redis에 저장
def save_article(article: Dict):
    """
    중요도(5, 4, 3)에 따라 Redis에 저장
    """
    if article['importance'] is None:
        return
    importance = int(article['importance'])
    if importance not in [5, 4, 3]:
        return
    key = f"important_articles_{importance}"
    now_ts = time.time()
    redis_client.zadd(key, {json.dumps(article): now_ts})
    logger.info(f"✅ 저장 완료: {key} - {article['id']}")

# ✅ 3. 특정 중요도 + 시간 범위에서 기사 가져오기
def load_articles(importance: int, start_ts: float, end_ts: float, limit: int) -> List[Dict]:
    """
    importance별 + 시간 범위내 기사 가져오기
    """
    key = f"important_articles_{importance}"
    raw_articles = redis_client.zrevrangebyscore(
        key,
        max=end_ts,
        min=start_ts,
        start=0,
        num=limit
    )
    return [json.loads(article) for article in raw_articles]

# ✅ 4. Redis에서 사용한 기사 삭제
def delete_articles(articles: List[Dict]):
    """
    Redis에서 사용 완료한 기사 삭제
    """
    for article in articles:
        if article['importance'] is None:
            continue
        importance = int(article['importance'])
        key = f"important_articles_{importance}"
        redis_client.zrem(key, json.dumps(article))
    logger.info(f"🗑️ 삭제 완료: {len(articles)} articles from {key}")

# ✅ 5. Top N 기사 가져오기 (신선도 + 중요도 우선)
def select_top_articles(top_n: int = 5) -> List[Dict]:
    """
    오늘 → 어제 → 그제 순으로 중요도 높은 기사 5개 뽑기
    5점 > 4점 > 3점 우선순위
    """
    now = time.time()
    ranges = [
        (now - 60*60*24, now),  # 오늘
        (now - 60*60*24*2, now - 60*60*24),  # 어제
        (now - 60*60*24*3, now - 60*60*24*2),  # 그제
    ]

    final_selection = []

    for importance in [5, 4, 3]:
        for start_ts, end_ts in ranges:
            candidates = load_articles(importance, start_ts, end_ts, limit=top_n - len(final_selection))
            final_selection.extend(candidates)
            if len(final_selection) >= top_n:
                break
        if len(final_selection) >= top_n:
            break

    return final_selection[:top_n]

