#!/usr/bin/env python3
"""
RSS 피드 패키지 기능 테스트 스크립트
"""
import os
import json
import logging
import sys
from rss_feed.feed_parser import FeedParser
from rss_feed.managers.redis_manager import RedisManager
from rss_feed.managers.s3_manager import S3Manager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def setup_test_data():
    """테스트 데이터 설정"""
    # 테스트 데이터 디렉토리
    os.makedirs("rss_feed/data", exist_ok=True)
    
    # 테스트 RSS 피드 데이터
    test_feeds = {
        "테스트_발행사": [
            "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
        ]
    }
    
    # 뉴스 파일 경로
    test_file_path = "rss_feed/data/news_file.json"
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        json.dump(test_feeds, f, ensure_ascii=False, indent=2)
    
    logger.info(f"테스트 데이터 생성 완료: {test_file_path}")
    return test_file_path

def test_redis_manager():
    """Redis 관리자 테스트"""
    logger.info("\n==== Redis 관리자 테스트 ====")
    # 실제 연결 없이 테스트
    redis_manager = RedisManager(host="localhost")
    
    test_url = "https://example.com/test-article"
    
    # 메소드 실행은 하지만 실제 연결은 무시
    logger.info(f"테스트 URL 해시: {redis_manager._create_hash(test_url)}")
    logger.info("Redis 관리자 테스트 완료")

def test_s3_manager():
    """S3 관리자 테스트"""
    logger.info("\n==== S3 관리자 테스트 ====")
    # 실제 연결 없이 테스트
    s3_manager = S3Manager(bucket_name="test-bucket")
    
    # 메소드 접근만 테스트
    logger.info(f"S3 버킷명: {s3_manager.bucket_name}")
    logger.info("S3 관리자 테스트 완료")
    
def test_feed_parser():
    """피드 파서 테스트"""
    logger.info("\n==== 피드 파서 테스트 ====")
    
    # 피드 파서 초기화 (Redis와 S3 연결 없이)
    parser = FeedParser()
    
    # 테스트 URL
    test_url = "https://example.com/test-article"
    test_publisher = "테스트_발행사"
    
    # 파일명 생성 테스트
    file_name = parser._generate_filename(test_url)
    logger.info(f"생성된 파일명: {file_name}")
    
    # HTML 디렉토리 확인
    logger.info(f"HTML 저장 디렉토리: {parser.html_dir}")
    
    logger.info("피드 파서 테스트 완료")

def main():
    """메인 테스트 함수"""
    logger.info("RSS 피드 패키지 테스트 시작")
    
    # 테스트 데이터 설정
    setup_test_data()
    
    # 각 컴포넌트 테스트
    test_redis_manager()
    test_s3_manager()
    test_feed_parser()
    
    logger.info("\n모든 테스트 완료! 패키지가 성공적으로 설치되었습니다.")

if __name__ == "__main__":
    main() 