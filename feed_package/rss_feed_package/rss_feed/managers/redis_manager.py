import redis
import os
import logging
from typing import Set, Dict, List
logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True,
                password=os.getenv('REDIS_PASSWORD')
            )
            self.key_prefix = "article:url:"
            # 연결 테스트
            self.redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
    
    def get_all_article_urls(self) -> Set[str]:
        """
        Redis에서 key_prefix에 해당하는 모든 키를 가져와서, URL 부분만 추출하여 집합으로 반환.
        """
        # Redis의 KEYS 명령은 프로덕션에서는 성능 이슈가 있을 수 있으나,
        # 4천개 정도라면 문제 없을 것으로 예상됨.
        keys = self.redis_client.keys(self.key_prefix + "*")
        # 각 키에서 접두사를 제거하고 실제 URL만 추출
        urls = {key[len(self.key_prefix):] for key in keys}
        return urls
    
    
    def _store_article(self, url: str, publisher: str) -> None:
        """
        새로운 기사를 redis에 저장.
        키는 "article:url:{url}" 형태로 저장하며, 값은 publisher로 저장.
        """
        key = self.key_prefix + url
        self.redis_client.set(key, publisher)

    def store_articles(self, articles: Dict[str, List[str]]) -> None:
        """여러 기사를 redis에 저장"""
        for publisher, urls in articles.items():
            for url in urls:
                self._store_article(url, publisher)
