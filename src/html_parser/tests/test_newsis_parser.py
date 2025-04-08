import pytest
from parser.newsis_parer import NewsisParser as Parser
from datetime import datetime

@pytest.fixture
def sample_html():
    with open('html/뉴시스/148efd740edcb31917ac84960cd0d69c.html', 'r', encoding='utf-8') as file:
        return file.read()

def get_publication_date(iso_str: str) -> str:
    # article:published_time meta 태그에서 발행일 추출
    dt = datetime.fromisoformat(iso_str)
    unix_timestamp = dt.timestamp()  # 초 단위 timestamp
    return unix_timestamp
    

def test_get_title(sample_html):
    """제목 파싱 테스트"""
    parser = Parser(sample_html)
    title = parser.get_title()
    assert title != ""
    assert isinstance(title, str)
    assert title == '"뉴진스, 법원마저 무시·혐한 발언…꿈에서 깨라"'


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "최지윤"

def test_get_publication_date(sample_html):
#     """발행 날짜 파싱 테스트"""
    parser = Parser(sample_html)
    publication_date = parser.get_publication_date()
    assert publication_date != ""
    assert isinstance(publication_date, float)
    print(publication_date)

def test_get_content(sample_html):
    """본문 파싱 테스트"""
    parser = Parser(sample_html)
    content = parser.get_content()
    test_text = '한국이 우리를 혁명가로 만들고 싶어 하는 것 같다"고 했다'
    assert content != ""
    assert isinstance(content, str)
    assert test_text in content
