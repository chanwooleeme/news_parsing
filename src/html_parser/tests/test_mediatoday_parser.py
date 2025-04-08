import pytest
from parser.mediatoday_parser import MediatodayParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/미디어오늘/6ac7ec566c0621b3e8743a1b8f69ed27.html', 'r', encoding='utf-8') as file:
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
    assert title == '언론을 믿을 수 없어 계엄을 택했다는 대통령'


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "미디어오늘"

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
    test_start = '윤석열 대통령 탄핵 심판 9차 변론에서 윤 대통령 측'
    test_middle = '론노동조합 조'
    test_end = '택했다는 황당한 주장이 헌법재판소에서 대통령측 입장으로 등장했다는 사실이 서글프다. '
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
    print(content)
