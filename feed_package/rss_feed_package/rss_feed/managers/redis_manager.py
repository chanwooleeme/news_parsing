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
            self.batch_size = 1000  # 배치 크기 설정
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
    
    def get_all_article_urls(self) -> Set[str]:
        """
        SCAN을 사용하여 모든 URL을 배치로 가져오기
        """
        urls = set()
        cursor = 0
        pattern = self.key_prefix + "*"
        
        while True:
            cursor, keys = self.redis_client.scan(
                cursor=cursor, 
                match=pattern, 
                count=self.batch_size
            )
            
            # URL 추출 (접두사 제거)
            urls.update(key[len(self.key_prefix):] for key in keys)
            
            # 모든 키를 순회했으면 종료
            if cursor == 0:
                break
                
        return urls
    
    
    def _store_article(self, url: str, publisher: str) -> None:
        """
        새로운 기사를 redis에 저장.
        키는 "article:url:{url}" 형태로 저장하며, 값은 publisher로 저장.
        """
        key = self.key_prefix + url
        self.redis_client.set(key, publisher)

    def store_articles(self, articles: Dict[str, List[str]]) -> None:
        """
        여러 기사를 redis에 일괄 저장
        TTL: 3일 (259,200초)
        """
        TTL_SECONDS = 3 * 24 * 3600  # 3일
        
        pipe = self.redis_client.pipeline()
        for publisher, urls in articles.items():
            for url in urls:
                key = self.key_prefix + url
                pipe.set(key, publisher)
                pipe.expire(key, TTL_SECONDS)
        
        pipe.execute()
        logger.info(f"Redis에 {sum(len(urls) for urls in articles.values())}개 URL 저장 (TTL: 3일)")

    def is_articles_processed(self, urls: List[str]) -> Dict[str, bool]:
        """
        여러 URL들의 처리 여부를 한 번에 확인
        
        Args:
            urls: 확인할 URL 리스트
            
        Returns:
            Dict[str, bool]: URL별 처리 여부 (True: 처리됨, False: 미처리)
        """
        pipe = self.redis_client.pipeline()
        keys = [self.key_prefix + url for url in urls]
        
        # EXISTS 명령어를 파이프라인으로 한 번에 실행
        for key in keys:
            pipe.exists(key)
        
        results = pipe.execute()
        return dict(zip(urls, results))
