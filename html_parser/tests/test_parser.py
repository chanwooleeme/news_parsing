import pytest
from bs4 import BeautifulSoup
from datetime import datetime
from html_parser.parser.base_parser import BaseParser
import re
from typing import Optional

def test_base_parser_exists():
    """BaseParser 클래스가 존재하는지 테스트"""
    assert BaseParser


def test_base_parser_init(sample_html):
    """파서 초기화 테스트"""
    parser = MockParser(sample_html)  # BaseParser 대신 MockParser 사용
    assert isinstance(parser.soup, BeautifulSoup)
    # BaseParser의 인스턴스인지도 확인
    assert isinstance(parser, BaseParser)

def test_base_parser_has_required_methods():
    """BaseParser가 필요한 메소드를 가지고 있는지 테스트"""
    # 클래스 자체의 속성을 검사
    assert hasattr(BaseParser, "get_title")
    assert hasattr(BaseParser, "get_author")
    assert hasattr(BaseParser, "get_publication_date")
    assert hasattr(BaseParser, "get_content")
    assert hasattr(BaseParser, "clean_text")
    assert hasattr(BaseParser, "extract_meta")
    assert hasattr(BaseParser, "parse")

class MockParser(BaseParser):
    """테스트를 위한 Mock 파서"""
    
    def get_content(self) -> str:
        content = self.soup.select_one('.content')
        return self.clean_text(content.text) if content else ""

@pytest.fixture
def sample_html():
    """테스트용 HTML 픽스처"""
    return """
    <html>
        <head>
            <title>HTML 제목</title>
            <meta property="og:title" content="메타 제목">
            <meta property="article:author" content="홍길동 기자">
            <meta property="article:published_time" content="2024-03-25T09:00:00+09:00">
        </head>
        <body>
            <h1>테스트 제목</h1>
            <div class="content">테스트 본문 내용</div>
            <div class="author">김철수 기자</div>
        </body>
    </html>
    """

def test_parser_initialization(sample_html):
    """파서 초기화 테스트"""
    parser = MockParser(sample_html)
    assert isinstance(parser.soup, BeautifulSoup)

def test_get_title(sample_html):
    """제목 파싱 테스트"""
    parser = MockParser(sample_html)
    # BaseParser의 get_title이 og:title meta 태그를 우선적으로 사용하는지 확인
    assert parser.get_title() == "메타 제목"

def test_get_content(sample_html):
    """본문 파싱 테스트"""
    parser = MockParser(sample_html)
    assert parser.get_content() == "테스트 본문 내용"

def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = MockParser(sample_html)
    # article:author meta 태그에서 추출한 후 '기자' 텍스트가 제거되는지 확인
    assert parser.get_author() == "홍길동"

def test_get_publication_date(sample_html):
    """날짜 파싱 테스트"""
    parser = MockParser(sample_html)
    # Unix 타임스탬프로 변환되는지 확인
    expected_timestamp = datetime(2024, 3, 25, 9, 0, 0).timestamp()
    assert parser.get_publication_date() == expected_timestamp

def test_extract_meta(sample_html):
    """메타데이터 추출 테스트"""
    parser = MockParser(sample_html)
    assert parser.extract_meta("og:title") == "메타 제목"
    assert parser.extract_meta("article:author") == "홍길동 기자"
    assert parser.extract_meta("non-existent") == ""

def test_clean_text():
    """텍스트 정제 테스트"""
    parser = MockParser("<html></html>")
    assert parser.clean_text("  테스트   텍스트  ") == "테스트 텍스트"
    assert parser.clean_text("") == ""
    assert parser.clean_text(None) == ""

def test_clean_author():
    """작성자 정제 테스트"""
    parser = MockParser("<html></html>")
    assert parser.clean_author("홍길동 기자") == "홍길동"
    assert parser.clean_author("김철수") == "김철수"
    assert parser.clean_author("") == ""

def test_parse_method(sample_html):
    """parse 메소드 테스트"""
    parser = MockParser(sample_html)
    result = parser.parse()
    assert isinstance(result, dict)
    assert result["title"] == "메타 제목"
    assert result["author"] == "홍길동"
    assert result["content"] == "테스트 본문 내용"
    assert "publication_date" in result

def test_css_selector_parsing():
    """CSS 선택자를 사용한 파싱 테스트"""
    html = """
    <html>
        <body>
            <div class="article">
                <h1 class="headline">CSS 선택자 테스트</h1>
                <div class="author-info">
                    <span class="author">이순신 기자</span>
                    <span class="email">lee@example.com</span>
                </div>
                <div class="content">
                    <p>첫 번째 문단</p>
                    <p>두 번째 문단</p>
                </div>
                <ul class="tags">
                    <li>뉴스</li>
                    <li>테스트</li>
                </ul>
            </div>
        </body>
    </html>
    """
    parser = MockParser(html)
    soup = parser.soup
    
    # 1. 단일 요소 선택
    headline = soup.select_one(".headline")
    assert headline.text == "CSS 선택자 테스트"
    
    # 2. 복수 요소 선택
    paragraphs = soup.select(".content p")
    assert len(paragraphs) == 2
    assert paragraphs[0].text == "첫 번째 문단"
    
    # 3. 자식 선택자
    author = soup.select_one(".author-info > .author")
    assert author.text == "이순신 기자"
    
    # 4. 속성 선택자 활용
    tags = soup.select("ul.tags li")
    assert len(tags) == 2
    assert [tag.text for tag in tags] == ["뉴스", "테스트"]

def test_handle_error_in_parsing():
    """파싱 중 오류 처리 테스트"""
    # 분석할 수 없는 형식의 날짜가 포함된 HTML
    html = """
    <html>
        <head>
            <meta property="article:published_time" content="invalid-date-format">
            <meta property="og:title" content="오류 테스트">
        </head>
        <body>
            <div class="content">오류 테스트 본문</div>
        </body>
    </html>
    """
    parser = MockParser(html)
    
    # 오류가 발생해도 parse 메소드가 결과를 반환해야 함
    result = parser.parse()
    assert result["title"] == "오류 테스트"
    assert "publication_date" in result  # 오류 시 현재 시간으로 설정됨
    assert result["content"] == "오류 테스트 본문"

