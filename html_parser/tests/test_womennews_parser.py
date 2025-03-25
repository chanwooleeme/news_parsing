import pytest
from parser.womennews_parser import WomennewsParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/여성신문/8ac1dd83900bdad2ff8a26890090fd02.html', 'rb') as file:
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
    assert title == "'황희찬 결승골' 대한민국, 포르투갈 꺾고 세번째 16강"


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "유영혁"

def test_get_publication_date(sample_html):
#     """발행 날짜 파싱 테스트"""
    parser = Parser(sample_html)
    publication_date = parser.get_publication_date()
    assert publication_date != ""
    assert isinstance(publication_date, float)
    threshold = datetime(2022, 12, 2, tzinfo=timezone.utc).timestamp()
    assert publication_date > threshold, f"Publication date ({publication_date}) is not after 2024-01-01 UTC ({threshold})."

def test_get_content(sample_html):
    """본문 파싱 테스트"""
    parser = Parser(sample_html)
    content = parser.get_content()
    test_start = '대한한국 축구가 포르투갈을 꺾고 사상 세번째 원정 월드컵 두 번째 16강 진출에 성공했다.'
    test_middle = '한국은 경기 시작 5분 만에 왼쪽 측면이 뚫리며 힘없이 선제골을 내줬다.'
    test_end = '하며 16강 진출의 기쁨을 누렸다.'
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
    
    print(content)