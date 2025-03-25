import pytest
from parser.ablenews_parser import AblenewsParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/에이블뉴스/b10f5c8b52cc3a9cbc6139b9582d3089.html', 'rb') as file:
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
    assert title == "신의현, 전국장애인동계체전 남자 크로스컨트리 3km ‘金’ 2관왕"


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "권중훈"

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
    test_start = '동계패럴림픽 대한민국 최초 금메달리스트 신의현'
    test_middle = '위를 기록한 것은 충분히 가능성을 보여줬다고 생각한다. 카누와 크로스컨트리스키를 병행하는 것은 쉽지 않은 선택'
    test_end = '계체전 마지막 날인 14일에는 크로스컨트리스키, 스노보드, 아이스하키, 컬링 경기가 진행되며 일정 및 결과는 대회 공식'
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
    
    print(content)