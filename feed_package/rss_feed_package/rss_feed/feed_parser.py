import feedparser
import requests
import hashlib
import os
import json
from typing import Dict, List, Optional
import logging
from .managers.redis_manager import RedisManager
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
    
    def _get_article_links_from_rss_xmls_for_test(self, test_count: int = 1) -> Dict[str, List[str]]:
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
        cnt = 0

        for publisher, xmls in rss_dict.items():
            publisher = publisher.rstrip()
            article_set = set()
            logger.info(f"\n{publisher} RSS 피드 파싱 시작: {len(xmls)}개 XML")
            
            for xml in xmls:
                cnt += 1
                if cnt > test_count:
                    break
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
            return response.content
        except Exception as e:
            logger.error(f"HTML 다운로드 실패 (URL: {url}): {e}")
            return None

    def _process_new_articles(self, new_articles: Dict[str, List[str]]) -> None:
        """새로운 기사들에 대한 추가 처리 (파싱, 임베딩, 벡터 저장)"""
        if not new_articles:
            logger.info("새로운 기사가 없어 추가 처리를 건너뜁니다.")
            return
        logger.info("추가 처리 완료")

    def _process_publisher_articles(self, publisher: str, urls: List[str], max_articles: Optional[int] = None) -> List[str]:
        """단일 발행사의 기사들을 처리
        
        Args:
            publisher: 발행사 이름
            urls: 처리할 URL 목록
            max_articles: 최대 처리할 기사 수 (None이면 전체 처리)
            
        Returns:
            처리된 새로운 URL 목록
        """
        target_urls = urls[:max_articles] if max_articles else urls
        logger.info(f"{publisher} 처리 시작: {len(target_urls)} 기사")
        
        # Redis에서 URL 처리 여부 확인
        processed_status = self.redis_manager.is_articles_processed(target_urls)
        new_urls = []
        
        for url, is_processed in processed_status.items():
            if not is_processed:
                if self._download_and_save_article(url, publisher):
                    new_urls.append(url)
                    
        if new_urls:
            logger.info(f"{publisher}: {len(new_urls)}개 새로운 기사 처리 완료")
        else:
            logger.info(f"{publisher}: 새로운 기사 없음")
            
        return new_urls

    def _download_and_save_article(self, url: str, publisher: str) -> bool:
        """단일 기사 다운로드 및 저장
        
        Returns:
            bool: 성공 여부
        """
        html_content = self._download_html(url)
        if html_content:
            file_path = self._save_html_locally(url, publisher, html_content)
            if file_path:
                logger.info(f"처리 완료: {url}")
                return True
        return False

    def _collect_and_process_articles(self, 
                                    urls_dict: Dict[str, List[str]], 
                                    target_publishers: Optional[List[str]] = None,
                                    max_per_publisher: Optional[int] = None) -> Dict[str, List[str]]:
        """기사 수집 및 처리 메인 로직
        
        Args:
            urls_dict: 발행사별 URL 딕셔너리
            target_publishers: 처리할 발행사 목록 (None이면 전체 처리)
            max_per_publisher: 발행사당 최대 처리 기사 수 (None이면 제한 없음)
        """
        # 발행사 필터링
        if target_publishers:
            urls_dict = {k: v for k, v in urls_dict.items() if k in target_publishers}
            
        new_articles = {}
        for publisher, urls in urls_dict.items():
            new_urls = self._process_publisher_articles(
                publisher=publisher,
                urls=urls,
                max_articles=max_per_publisher
            )
            if new_urls:
                new_articles[publisher] = new_urls
                
        # 새로운 기사 Redis에 저장
        if new_articles:
            self.redis_manager.store_articles(new_articles)
            
        return new_articles

    def process_feeds(self) -> None:
        """전체 기사 처리 파이프라인"""
        # 1. RSS 피드에서 URL 수집
        urls_by_publisher = self._get_article_links_from_rss_xmls()
        if not urls_by_publisher:
            logger.error("기사 링크 수집 실패")
            return
        logger.info(f"1단계 완료: {len(urls_by_publisher)}개 발행사의 URL 수집")

        # 2. Redis에서 새로운 URL 필터링
        new_urls_by_publisher = self._filter_new_urls(urls_by_publisher)
        if not new_urls_by_publisher:
            logger.info("2단계 완료: 새로운 URL 없음")
            return
        logger.info(f"2단계 완료: {sum(len(urls) for urls in new_urls_by_publisher.values())}개의 새 URL 발견")

        # 3. HTML 다운로드 및 로컬 저장
        downloaded_articles = self._download_and_save_articles(new_urls_by_publisher)
        if not downloaded_articles:
            logger.error("3단계 완료: 다운로드 실패")
            return
        logger.info(f"3단계 완료: {sum(len(urls) for urls in downloaded_articles.values())}개 기사 저장")

        # 4. Redis에 처리 완료 표시
        self._mark_articles_as_processed(downloaded_articles)
        logger.info("4단계 완료: Redis 업데이트")

        # 5. 추가 처리 (임베딩, 벡터 저장 등)
        self._process_new_articles(downloaded_articles)
        logger.info("5단계 완료: 추가 처리 완료")

    def _filter_new_urls(self, urls_by_publisher: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Redis 체크를 통해 새로운 URL만 필터링"""
        new_urls_by_publisher = {}
        
        for publisher, urls in urls_by_publisher.items():
            processed_status = self.redis_manager.is_articles_processed(urls)
            new_urls = [url for url, is_processed in processed_status.items() 
                       if not is_processed]
            
            if new_urls:
                new_urls_by_publisher[publisher] = new_urls
                logger.info(f"- {publisher}: {len(new_urls)}/{len(urls)} 새로운 URL")
                
        return new_urls_by_publisher

    def _download_and_save_articles(self, urls_by_publisher: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """HTML 다운로드 및 로컬 저장"""
        downloaded_articles = {}
        
        for publisher, urls in urls_by_publisher.items():
            successful_urls = []
            logger.info(f"- {publisher} 다운로드 시작: {len(urls)}개 URL")
            
            for url in urls:
                if self._download_and_save_article(url, publisher):
                    successful_urls.append(url)
                    
            if successful_urls:
                downloaded_articles[publisher] = successful_urls
                logger.info(f"- {publisher} 완료: {len(successful_urls)}/{len(urls)} 성공")
                
        return downloaded_articles

    def _mark_articles_as_processed(self, articles_by_publisher: Dict[str, List[str]]) -> None:
        """처리 완료된 기사를 Redis에 표시"""
        self.redis_manager.store_articles(articles_by_publisher)

    def process_feeds_for_test(self, 
                             target_publishers: List[str] = ["경향신문", "뉴시스"], 
                             max_html_per_publisher: int = 5) -> None:
        """테스트용 기사 처리 파이프라인"""
        # 1. 테스트용 RSS 피드에서 URL 수집 (제한된 수만)
        urls_by_publisher = self._get_article_links_from_rss_xmls_for_test()
        if not urls_by_publisher:
            logger.error("기사 링크 수집 실패")
            return

        # 2. 지정된 발행사만 필터링 & URL 수 제한
        filtered_urls = {
            publisher: urls[:max_html_per_publisher]
            for publisher, urls in urls_by_publisher.items()
            if publisher in target_publishers
        }
        logger.info(f"1단계 완료: {len(filtered_urls)}개 발행사 선택")

        # 3~5. 실제 처리 파이프라인과 동일
        new_urls_by_publisher = self._filter_new_urls(filtered_urls)
        if not new_urls_by_publisher:
            return

        downloaded_articles = self._download_and_save_articles(new_urls_by_publisher)
        if not downloaded_articles:
            return

        self._mark_articles_as_processed(downloaded_articles)
        self._process_new_articles(downloaded_articles)

def main():
    parser = FeedParser()
    parser.process_feeds()

if __name__ == "__main__":
    main()