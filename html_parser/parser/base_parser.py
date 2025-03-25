from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Dict, Any
import re

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
    
    def parse(self) -> dict:
        """
        전체 HTML을 파싱하여 기사 정보를 딕셔너리로 반환.
        """
        return {
            'title': self.get_title(),
            'author': self.get_author(),
            'publication_date': self.get_publication_date(),
            'content': self.get_content(),
        }
    
    def get_title(self) -> str:
        """기사 제목을 반환합니다."""
        return self.soup.find('h1', class_='title').text.strip()
    
    def get_author(self) -> str:
        """기사 작성자를 반환합니다."""
        return self.soup.find('span', class_='author').text.strip() 
    
    def get_publication_date(self) -> str:
        """기사 발행 날짜를 반환합니다."""
        return self.soup.find('span', class_='date').text.strip()
    
    def get_content(self) -> str:
        """기사 본문을 반환합니다."""
        return self.soup.find('div', class_='body').text.strip()