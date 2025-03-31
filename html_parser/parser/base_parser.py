from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging

class BaseParser(ABC):
    """HTML 문서 파싱을 위한 기본 파서 클래스"""
    
    def __init__(self, html: str):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')

    def clean_text(self, text: str) -> str:
        """
        불필요한 공백, 줄바꿈 등을 제거하는 유틸리티 함수.
        """
        if text:
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        return ''
    
    def extract_meta(self, property_name: str) -> str:
        """
        주어진 meta property 또는 name으로부터 content 값을 추출하는 함수.
        """
        tag = self.soup.find("meta", property=property_name)
        if tag and tag.get("content"):
            return self.clean_text(tag.get("content"))
        tag = self.soup.find("meta", attrs={"name": property_name})
        if tag and tag.get("content"):
            return self.clean_text(tag.get("content"))
        return ''
    
    def get_category(self) -> str:
        category = self.extract_meta("article:section")
        if category:
            return category
        else:
            category = self.extract_meta("Classification")
            if category:
                return category
        return ''
    
    def parse(self) -> dict:
        """
        전체 HTML을 파싱하여 기사 정보를 딕셔너리로 반환.
        """
        try:
            return {
                'title': self.get_title(),
                'author': self.get_author(),
                'category': self.get_category(),
                'publication_date': self.get_publication_date(),
                'content': self.get_content(),
            }
        except Exception as e:
            logging.error(f"파싱 중 예외 발생: {e}")
            # 최소한의 정보라도 반환
            return {
                'title': self.get_title() or '제목 없음',
                'author': '',
                'category': '',
                'publication_date': datetime.now().timestamp(),
                'content': '',
                'error': str(e)
            }
    
    def get_title(self) -> str:
        # 우선 og:title meta 태그에서 제목 추출
        title = self.extract_meta("og:title")
        if title:
            return title
        # fallback: <title> 태그 사용
        title_tag = self.soup.find("title")
        if title_tag:
            return self.clean_text(title_tag.get_text())
        return ''
    
    def get_author(self) -> str:
        # article:author meta 태그를 우선 사용
        author = self.extract_meta("article:author")
        return self.clean_author(author)
    
    def get_publication_date(self) -> str:
        # article:published_time meta 태그에서 발행일 추출
        try:
            iso_str = self.extract_meta("article:published_time")
            if not iso_str:
                # 대안으로 다른 메타 태그 확인
                iso_str = self.extract_meta("meta:pubdate") or self.extract_meta("pubdate")
                
            if not iso_str:
                # 발행일을 찾을 수 없는 경우 현재 시간 사용
                return datetime.now().timestamp()
                
            dt = datetime.fromisoformat(iso_str)
            unix_timestamp = dt.timestamp()  # 초 단위 timestamp
            return unix_timestamp
        except (ValueError, TypeError) as e:
            # ISO 형식이 아닌 경우 현재 시간으로 대체
            logging.error(f"발행일 파싱 오류: {e}")
            return datetime.now().timestamp()
    
    @abstractmethod
    def get_content(self) -> str:
        pass
    
    def clean_author(self, author: str) -> str:
        if '기자' in author:
            return re.sub(r'\s*기자\s*$', '', author)
        return author
