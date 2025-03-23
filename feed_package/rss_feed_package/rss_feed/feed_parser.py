import feedparser
import requests
import os
import json
import shutil
from typing import Dict, List, Optional, Tuple, Set
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

        for publisher in rss_dict.keys():
            article_set = set()
            for xml_link in rss_dict[publisher]:
                try:
                    feed = feedparser.parse(xml_link)
                    article_set.update(entry.link for entry in feed.entries)
                    logger.info(f"- {xml_link}: {len(feed.entries)}개 기사 발견")
                except Exception as e:
                    logger.error(f"RSS 파싱중 오류 발생 (URL: {xml_link}): {e}")

            article_dict[publisher] = list(article_set)
            total_articles += len(article_set)
            logger.info(f"{publisher} 처리 완료: {len(article_set)}개 고유 기사")
        
        logger.info(f"\n전체 처리 완료: {len(article_dict)}개 발행사, 총 {total_articles}개 기사")
        return article_dict

    def _generate_filename(self, url: str) -> str:
        """URL 기반 파일명 생성 - 해시 사용"""
        import hashlib
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

    def _download_new_articles(self, article_urls_dict: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, str]]]:
        """새로운 기사 다운로드"""
        new_articles_to_upload = {}  # {publisher: [(url, file_path), ...]}
        
        for publisher, urls in article_urls_dict.items():
            new_urls_with_paths = []
            logger.info(f"\n{publisher} 처리 시작: {len(urls)} 기사")
            
            for url in urls:
                # Redis에서 URL 확인 (해싱 없이 URL 그대로 사용)
                logger.info(f"새 URL 발견: {url}")
                html_content = self._download_html(url)
                if html_content:
                    file_path = self._save_html_locally(url, publisher, html_content)
                    if file_path:
                        new_urls_with_paths.append((url, file_path))
            
            if new_urls_with_paths:
                new_articles_to_upload[publisher] = new_urls_with_paths
                logger.info(f"{publisher}: {len(new_urls_with_paths)}개 새 기사 다운로드 완료")
            else:
                logger.info(f"{publisher}: 새로운 기사 없음")
                
        return new_articles_to_upload

    def _upload_to_s3_and_update_redis(self, new_articles_to_upload: Dict[str, List[Tuple[str, str]]]) -> Dict[str, List[str]]:
        """S3에 업로드하고 Redis 업데이트"""
        for publisher, url_path_pairs in new_articles_to_upload.items():
            
            for url, file_path in url_path_pairs:
                s3_key = f"{publisher}/{os.path.basename(file_path)}"
                
                # S3 업로드
                if self.s3_manager.upload_file(file_path, s3_key):
                    logger.info(f"S3 업로드 성공 및 Redis 업데이트: {url}")
                else:
                    logger.error(f"S3 업로드 실패: {url}")

    def _clean_html_directory(self) -> None:
        """S3 업로드 완료 후 HTML 디렉토리 정리"""
        try:
            if os.path.exists(self.html_dir):
                for publisher_dir in os.listdir(self.html_dir):
                    publisher_path = os.path.join(self.html_dir, publisher_dir)
                    if os.path.isdir(publisher_path):
                        shutil.rmtree(publisher_path)
                        logger.info(f"디렉토리 삭제 완료: {publisher_path}")
                logger.info("HTML 디렉토리 정리 완료")
        except Exception as e:
            logger.error(f"HTML 디렉토리 정리 중 오류 발생: {e}")

    def _remove_duplicated_articles(self, article_urls_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """중복 기사 제거: redis에 없는 새로운 기사만 반환"""
        existing_urls = self.redis_manager.get_all_article_urls()
        new_articles: Dict[str, List[str]] = {}

        for publisher, urls in article_urls_dict.items():
            for url in urls:
                # redis에 없는 URL이면 새로운 기사로 처리
                if url not in existing_urls:
                    if publisher not in new_articles:
                        new_articles[publisher] = []
                    new_articles[publisher].append(url)

        self.redis_manager.store_articles(new_articles)
        # 사용한 메모리를 해제 (옵션)
        del existing_urls
        return new_articles
    

    def process_feeds(self) -> None:
        """메인 처리 함수 - 단계별로 분리된 함수 호출"""
        # 1. RSS 피드에서 기사 링크 수집
        article_urls_dict = self._get_article_links_from_rss_xmls()
        if not article_urls_dict:
            logger.error("기사 링크 수집 실패")
            return
        
        # 2. redis에 저장된 중복 기사 제거
        article_urls_dict = self._remove_duplicated_articles(article_urls_dict)

        # 3. 새로운 기사 다운로드
        new_articles_to_upload = self._download_new_articles(article_urls_dict)
        
        # 3. S3에 업로드 및 Redis 업데이트
        self._upload_to_s3_and_update_redis(new_articles_to_upload)

        logger.info("모든 처리 완료")


def main():
    parser = FeedParser()
    parser.process_feeds()

if __name__ == "__main__":
    main()