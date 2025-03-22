import feedparser
import requests
import hashlib
import os
import json
from typing import Dict, List, Optional
import logging
from .managers.redis_manager import RedisManager
from .managers.s3_manager import S3Manager
import pkg_resources

logger = logging.getLogger(__name__)

class FeedParser:
    def __init__(self):
        current_dir = os.getcwd()
        # 환경 변수 기반 경로 설정
        self.html_dir = os.getenv('RSS_FEED_HTML_DIR', os.path.join(current_dir, "html"))
        
        # 뉴스 파일 경로 설정
        self.news_file_path = pkg_resources.resource_filename('rss_feed', 'data/news_file.json')
        
        # 관리자 객체 초기화
        self.redis_manager = RedisManager()
        # S3 버킷 이름 추가
        self.s3_manager = S3Manager()
        
        logger.info(f"초기화 완료: HTML 저장 경로 {self.html_dir}, 뉴스 파일 경로 {self.news_file_path}")

    def _get_article_links_from_rss_xmls(self) -> Dict[str, List[str]]:
        """RSS 피드에서 기사 링크 수집"""
        try:
            logger.info("RSS 피드 파일 읽기 시작")
            with open(self.news_file_path, "r", encoding='utf-8') as f:
                rss_dict = json.load(f)
            logger.info(f"RSS 피드 파일 읽기 완료: {len(rss_dict)} 발행사")
        except Exception as e:
            logger.error(f"파일 읽는중 오류 발생: {e}")
            return {}
        
        article_dict = {}
        total_articles = 0

        for publisher, xmls in rss_dict.items():
            publisher = publisher.rstrip()
            article_set = set()
            logger.info(f"\n{publisher} RSS 피드 파싱 시작: {len(xmls)}개 XML")
            
            for xml in xmls:
                try:
                    feed = feedparser.parse(xml)
                    article_count = len(feed.entries)
                    article_set.update(entry.link for entry in feed.entries)
                    logger.info(f"- {xml}: {article_count}개 기사 발견")
                except Exception as e:
                    logger.error(f"RSS 파싱중 오류 발생 (URL: {xml}): {e}")
            
            article_dict[publisher] = list(article_set)
            total_articles += len(article_set)
            logger.info(f"{publisher} 처리 완료: {len(article_set)}개 고유 기사")
        
        logger.info(f"\n전체 처리 완료: {len(article_dict)}개 발행사, 총 {total_articles}개 기사")
        return article_dict

    def _generate_filename(self, url: str) -> str:
        """URL 기반 파일명 생성"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"{url_hash}.html"

    def _save_html_locally(self, url: str, publisher: str, html_content: bytes) -> Optional[str]:
        """HTML을 로컬에 저장"""
        try:
            publisher_dir = os.path.join(self.html_dir, publisher)
            os.makedirs(publisher_dir, exist_ok=True)

            file_name = self._generate_filename(url)
            file_path = os.path.join(publisher_dir, file_name)

            with open(file_path, 'wb') as f:
                f.write(html_content)
            logger.info(f"로컬 저장 성공: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"로컬 저장 실패 (URL: {url}): {e}")
            return None

    def _download_html(self, url: str) -> Optional[bytes]:
        """HTML 다운로드"""
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            logger.info(f"HTML 다운로드 성공 (URL: {url})")
            return response.content
        except Exception as e:
            logger.error(f"HTML 다운로드 실패 (URL: {url}): {e}")
            return None

    def _process_new_articles(self, new_articles: Dict[str, List[str]]) -> None:
        """새로운 기사들에 대한 추가 처리 (파싱, 임베딩, 벡터 저장)"""
        if not new_articles:
            logger.info("새로운 기사가 없어 추가 처리를 건너뜁니다.")
            return

        logger.info("새로운 기사에 대한 추가 처리 시작")
        # TODO: parse_html 구현
        # TODO: embedding 구현
        # TODO: vector store 저장 구현
        logger.info("추가 처리 완료")

    def process_feeds(self) -> None:
        """메인 처리 함수"""
        # 1. RSS 피드에서 기사 링크 수집
        article_urls_dict = self._get_article_links_from_rss_xmls()
        if not article_urls_dict:
            logger.error("기사 링크 수집 실패")
            return
        
        # 2. 새로운 기사 다운로드 및 S3 업로드
        new_articles = {}
        for publisher, urls in article_urls_dict.items():
            new_urls = []
            logger.info(f"\n{publisher} 처리 시작: {len(urls)} 기사")
            
            for url in urls:
                # 테스트를 위해 Redis 검사를 우회 (모든 URL을 새 URL로 처리)
                # 실제 환경에서는 다시 활성화
                # if self.redis_manager.is_new_url(url):
                if True:  # 테스트용 우회
                    html_content = self._download_html(url)
                    if html_content:
                        file_path = self._save_html_locally(url, publisher, html_content)
                        if file_path:
                            s3_key = f"{publisher}/{os.path.basename(file_path)}"
                            # S3 업로드 우회
                            # if self.s3_manager.upload_file(file_path, s3_key):
                            #     self.redis_manager.mark_url_as_processed(url)
                            #     new_urls.append(url)
                            # 테스트를 위해 S3 업로드 성공으로 처리
                            logger.info(f"S3 업로드 생략 (테스트 모드): {s3_key}")
                            new_urls.append(url)
            
            if new_urls:
                new_articles[publisher] = new_urls
                logger.info(f"{publisher}: {len(new_urls)}개 새로운 기사 처리 완료")
            else:
                logger.info(f"{publisher}: 새로운 기사 없음")

        # 3. 새로운 기사에 대한 추가 처리
        self._process_new_articles(new_articles)

def main():
    parser = FeedParser()
    parser.process_feeds()

if __name__ == "__main__":
    main()