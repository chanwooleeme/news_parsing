# common/redis_manager.py

import redis
import os
from typing import List, Dict, Optional
from common.logger import get_logger
from common.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
logger = get_logger(__name__)

class RedisManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                password=REDIS_PASSWORD
            )
            self.redis_client.ping()  # ✅ 이거 꼭 넣어야함
            self.batch_size = 1000
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")

    def scan_keys(self, pattern: str) -> List[str]:
        cursor = 0
        keys = []

        while True:
            cursor, batch = self.redis_client.scan(cursor=cursor, match=pattern, count=self.batch_size)
            keys.extend(batch)
            if cursor == 0:
                break

        return keys

    def set_key(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        self.redis_client.set(key, value)
        if ttl:
            self.redis_client.expire(key, ttl)

    def batch_set_keys(self, items: Dict[str, str], ttl: Optional[int] = None) -> None:
        pipe = self.redis_client.pipeline()
        for key, value in items.items():
            pipe.set(key, value)
            if ttl:
                pipe.expire(key, ttl)
        pipe.execute()

    def exists_keys(self, keys: List[str]) -> List[bool]:
        pipe = self.redis_client.pipeline()
        for key in keys:
            pipe.exists(key)
        return pipe.execute()
