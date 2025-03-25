import pytest
from bs4 import BeautifulSoup
from datetime import datetime
from html_parser.parser.base_parser import BaseParser
import re

def test_base_parser_exists():
    """BaseParser 클래스가 존재하는지 테스트"""
    assert BaseParser


def test_base_parser_init(sample_html):
    """파서 초기화 테스트"""
    parser = MockParser(sample_html)  # BaseParser 대신 MockParser 사용
    assert isinstance(parser.soup, BeautifulSoup)
    # BaseParser의 인스턴스인지도 확인
    assert isinstance(parser, BaseParser)

def test_base_parser_has_parse_method():
    """BaseParser가 필요한 파싱 메소드를 가지고 있는지 테스트"""
    # 클래스 자체의 속성을 검사
    assert hasattr(BaseParser, "parse_title")
    assert hasattr(BaseParser, "parse_content")
    assert hasattr(BaseParser, "parse_date")
    assert hasattr(BaseParser, "parse_metadata")
    assert hasattr(BaseParser, "clean_text")

class MockParser(BaseParser):
    """테스트를 위한 Mock 파서"""
    
    def parse_title(self) -> str:
        title = self.soup.select_one('h1')
        return self.clean_text(title.text) if title else ""
    
    def parse_content(self) -> str:
        content = self.soup.select_one('.content')
        return self.clean_text(content.text) if content else ""

@pytest.fixture
def sample_html():
    """테스트용 HTML 픽스처"""
    return """
    <html>
        <head>
            <meta property="og:title" content="메타 제목">
            <meta property="article:published_time" content="2024-03-25T09:00:00+09:00">
        </head>
        <body>
            <h1>테스트 제목</h1>
            <div class="content">테스트 본문 내용</div>
        </body>
    </html>
    """

def test_parser_initialization(sample_html):
    """파서 초기화 테스트"""
    parser = MockParser(sample_html)
    assert isinstance(parser.soup, BeautifulSoup)

def test_parse_title(sample_html):
    """제목 파싱 테스트"""
    parser = MockParser(sample_html)
    assert parser.parse_title() == "테스트 제목"

def test_parse_content(sample_html):
    """본문 파싱 테스트"""
    parser = MockParser(sample_html)
    assert parser.parse_content() == "테스트 본문 내용"

def test_parse_date(sample_html):
    """날짜 파싱 테스트"""
    parser = MockParser(sample_html)
    assert parser.parse_date() == datetime(2024, 3, 25)

def test_parse_metadata(sample_html):
    """메타데이터 파싱 테스트"""
    parser = MockParser(sample_html)
    metadata = parser.parse_metadata()
    assert metadata.get('title') == "메타 제목"

def test_clean_text():
    """텍스트 정제 테스트"""
    parser = MockParser("<html></html>")
    assert parser.clean_text("  테스트   텍스트  ") == "테스트 텍스트"
    assert parser.clean_text("") == ""
    assert parser.clean_text(None) == ""

def test_parse_invalid_date(sample_html):
    """잘못된 날짜 형식 처리 테스트"""
    html = "<html><meta property='article:published_time' content='invalid-date'></html>"
    parser = MockParser(html)
    assert parser.parse_date() is None

def test_missing_elements():
    """필수 요소 누락 테스트"""
    parser = MockParser("<html></html>")
    assert parser.parse_title() == ""
    assert parser.parse_content() == ""

