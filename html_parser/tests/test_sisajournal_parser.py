import pytest
from parser.sisajournal_parser import SisajournalParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/시사저널/b24582994b6b2bbd7dcb9eb869a8de89.html', 'rb') as file:
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
    assert title == "‘이정섭 검사 비위 의혹’ 겨눈 공수처…대검 압수수색"


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "이혜영"

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
    test_start = '고위공직자범죄수사처(공수처)가 이정섭 대전고검 검사의 비위 의혹과 관련해 대검찰청을 압수수색했다. 검찰이 공소시효'
    test_middle = '의 중 자녀의 초등학교 입학을 위한 위장전입, 대기업 임원으로부터 리조트 객실료 수수, 처가가 운영하는 골프장 직원과 가사도우미'
    test_end = '재판소는 지난해 8월 기각했다.'
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
    
    print(content)