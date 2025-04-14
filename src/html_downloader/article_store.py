from typing import Dict, List, Set
from .redis_manager import RedisManager
from logger import get_logger

logger = get_logger("article_store")

class ArticleStore:
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        self.key_prefix = "article:url:"
        self.ttl_seconds = 3 * 24 * 3600  # 3일

    def _format_key(self, url: str) -> str:
        return f"{self.key_prefix}{url}"

    def get_all_article_urls(self) -> Set[str]:
        pattern = self.key_prefix + "*"
        keys = self.redis_manager.scan_keys(pattern)
        return {key[len(self.key_prefix):] for key in keys}

    def store_articles(self, articles: Dict[str, List[str]]) -> None:
        batch = {}
        for publisher, urls in articles.items():
            for url in urls:
                key = self._format_key(url)
                batch[key] = publisher

        self.redis_manager.batch_set_keys(batch, ttl=self.ttl_seconds)
        logger.info(f"Redis에 {len(batch)}개 URL 저장 (TTL: 3일)")

    def is_articles_processed(self, urls: List[str]) -> Dict[str, bool]:
        keys = [self._format_key(url) for url in urls]
        exists_results = self.redis_manager.exists_keys(keys)
        return dict(zip(urls, exists_results))

