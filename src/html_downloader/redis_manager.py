from redis import Redis
from typing import List, Dict, Optional, Any, Set
from logger import get_logger   
import json

logger = get_logger("redis_manager")

class RedisManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.logger = logger

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Redis에 데이터 저장"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.redis.set(key, value)
            if expire:
                self.redis.expire(key, expire)
            return True
        except Exception as e:
            logger.error(f"Redis 저장 실패: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Redis에서 데이터 조회"""
        try:
            value = self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis 조회 실패: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Redis에서 데이터 삭제"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis 삭제 실패: {e}")
            return False

    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis 키 확인 실패: {e}")
            return False

    def scan_keys(self, pattern: str) -> List[str]:
        """Redis에서 패턴에 맞는 키들을 스캔하여 반환"""
        try:
            cursor = 0
            keys = []
            while True:
                cursor, batch = self.redis.scan(cursor, match=pattern)
                keys.extend(batch)
                if cursor == 0:
                    break
            return keys
        except Exception as e:
            logger.error(f"Redis scan 실패: {e}")
            return []

    def batch_set_keys(self, items: Dict[str, str], ttl: int = None) -> None:
        """여러 키-값 쌍을 한 번에 Redis에 저장"""
        try:
            pipeline = self.redis.pipeline()
            for key, value in items.items():
                if ttl:
                    pipeline.setex(key, ttl, value)
                else:
                    pipeline.set(key, value)
            pipeline.execute()
        except Exception as e:
            logger.error(f"Redis batch set 실패: {e}")

    def exists_keys(self, keys: List[str]) -> List[bool]:
        """주어진 키들이 Redis에 존재하는지 확인"""
        try:
            pipeline = self.redis.pipeline()
            for key in keys:
                pipeline.exists(key)
            return pipeline.execute()
        except Exception as e:
            logger.error(f"Redis exists 실패: {e}")
            return [False] * len(keys)
