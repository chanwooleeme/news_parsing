import pytest
from parser.chosun_parser import ChosunParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/조선일보/87201a238c8a73082fff2ae68d86a216.html', 'rb') as file:
        content = file.read()
    
    # 에러 무시하고 디코딩 ('replace'는 잘못된 문자를 ''로 대체)
    return content.decode('utf-8', errors='replace')

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
    assert title == "NYT “트럼프의 복수 투어”...바이든·해리스·힐러리 기밀접근권 박탈"


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "재인 유"

def test_get_publication_date(sample_html):
#     """발행 날짜 파싱 테스트"""
    parser = Parser(sample_html)
    publication_date = parser.get_publication_date()
    assert publication_date != ""
    assert isinstance(publication_date, float)
    threshold = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    assert publication_date > threshold, f"Publication date ({publication_date}) is not after 2024-01-01 UTC ({threshold})."

def test_get_content(sample_html):
    """본문 파싱 테스트"""
    parser = Parser(sample_html)
    content = parser.get_content()
    test_start = '국 일간 뉴욕타임스(NYT)에 따르면 트럼프는 이날 트럼프 대통령은 바이든 전 대통령, 해리스 전 부통령, 힐러리 클린턴 전 국무장관 등을 포함해 기밀 취급 인가 및 접근권을 취소하는 '
    test_middle = '맨해튼지검 검사장 등을 목록에 포함시켰다. 이외에도'
    test_end = '적(敵)의 목록처럼 읽힌다”고 '
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
    
    print(content)