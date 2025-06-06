import os
import hashlib
import feedparser
import requests
import sys
from typing import Dict, List, Optional
from logger import get_logger
from .article_store import ArticleStore
from html_downloader.redis_manager import RedisManager
from redis import Redis

logger = get_logger("html_downloader")

class HtmlDownloaderConfig:
    def __init__(self, html_dir: str, redis_client: Redis, ttl_seconds: int = 3 * 24 * 3600):
        self.html_dir = html_dir
        self.ttl_seconds = ttl_seconds  # TTL 기본값은 3일
        
        # Redis 연결 시도
        try:
            self.redis = redis_client
            # 연결 테스트
            self.redis.ping()
            logger.info("✅ Redis 연결 성공")
        except Exception as e:
            logger.error(f"❌ Redis 연결 실패: {e}")
            sys.exit(1)  # Redis 연결 실패 시 프로그램 종료

class HtmlDownloader:
    def __init__(self, config: HtmlDownloaderConfig):
        self.config = config
        redis_manager = RedisManager(config.redis)
        self.article_store = ArticleStore(redis_manager)

    @staticmethod
    def _generate_filename(url: str) -> str:
        return f"{hashlib.md5(url.encode()).hexdigest()}.html"

    def _save_html(self, publisher: str, url: str, content: bytes) -> str:
        publisher_dir = os.path.join(self.config.html_dir, publisher)
        os.makedirs(publisher_dir, exist_ok=True)

        filename = self._generate_filename(url)
        filepath = os.path.join(publisher_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(content)

        logger.info(f"✅ 저장 완료: {filepath}")
        return filepath

    def _download_html(self, url: str) -> Optional[bytes]:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.warning(f"❌ 다운로드 실패: {url}, 오류: {e}")
            return None

    def download_articles(self, rss_links_by_publisher: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        RSS 수집 결과를 받아서 새로운 기사만 다운로드하고 저장.
        
        Args:
            rss_links_by_publisher (publisher -> [urls])

        Returns:
            저장 성공한 기사들 (publisher -> [urls])
        """
        results = {}

        for publisher, urls in rss_links_by_publisher.items():
            logger.info(f"📰 {publisher} 처리 시작 ({len(urls)}개 URL)")

            # ✅ Redis로 필터링: 아직 저장 안된 URL만
            processed_status = self.article_store.is_articles_processed(urls)
            new_urls = [url for url, processed in processed_status.items() if not processed]

            saved_urls = []
            for url in new_urls:
                content = self._download_html(url)
                if content:
                    self._save_html(publisher, url, content)
                    saved_urls.append(url)

            if saved_urls:
                results[publisher] = saved_urls
                self.article_store.store_articles({publisher: saved_urls})
                logger.info(f"✅ {publisher} 다운로드 완료 ({len(saved_urls)}개)")

        return results

    @staticmethod
    def parse_rss_sources(rss_urls_by_publisher: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        외부에서 받은 RSS 주소를 파싱해서 기사 링크 모으기.
        """
        article_links = {}

        for publisher, feed_urls in rss_urls_by_publisher.items():
            links = set()
            for feed_url in feed_urls:
                try:
                    feed = feedparser.parse(feed_url)
                    links.update(entry.link for entry in feed.entries)
                except Exception as e:
                    logger.warning(f"❌ RSS 파싱 실패: {feed_url}, 오류: {e}")

            article_links[publisher] = list(links)
            logger.info(f"📄 {publisher}: {len(links)}개 기사 수집")

        return article_links
