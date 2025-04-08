import pytest
from parser.labortoday_parser import LabortodayParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/매일노동뉴스/c2b6f3b0ecf35082d31df984ec388eed.html', 'r', encoding='utf-8') as file:
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
    assert title == '시니어 카페 바리스타 vs 지하철 안내'


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "이동철"

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
    test_start = '아내는 젊은 노동자가 대다수인 커피가게와 달리 고령 노동자가 커피를 만드는 바'
    test_middle = '것도 없이 가만히 서서 오가는 사람을 쳐다'
    test_end = '욕구를 제대로 실현하는 방향으로 일자리 설계가 시급하다'
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
