import redis
import hashlib
import os
from typing import Optional


class RedisManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', '34.47.92.81'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True,
            password=os.getenv('REDIS_PASSWORD')
        )
        self.key_prefix = "article:url:"
    
    def is_new_url(self, url: str) -> bool:
        """URL이 새로운 것인지 확인"""
        url_hash = self._create_url_hash(url)
        return not self.redis_client.exists(f"{self.key_prefix}{url_hash}")
    
    def mark_url_as_processed(self, url: str) -> None:
        """URL을 처리 완료로 표시"""
        url_hash = self._create_url_hash(url)
        self.redis_client.set(f"{self.key_prefix}{url_hash}", "1")
    
    def _create_url_hash(self, url: str) -> str:
        """URL의 해시값 생성"""
        return hashlib.md5(url.encode()).hexdigest() 