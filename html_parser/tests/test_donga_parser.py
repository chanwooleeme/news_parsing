import pytest
from parser.donga_parser import DongaParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/동아일보/1593f9f3f27d4cd3d985ade415d3758f.html', 'r', encoding='utf-8') as file:
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
    assert title == '30주년 맞은 뮤지컬 ‘명성황후 ’주연 맡은 김소현 손준호 부부'


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "사지원"

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
    test_start = '“손준호 씨가 연기할 때 흔들림 없는 고목나무 같은 점이 부러워요.” (뮤지컬 배우 김소현)'
    test_end = '10년 동안 네 시즌에 걸쳐 명성황후로 살아온 김소현에게는 올해 공연은 더욱 특별하다. 16일 200회 공연을 앞두고 있기 때문이다. 한 배우가 단일 공연으로 달성하기 쉽지 않은 숫자다. 김소현은 “뮤지컬 배우는 선택하는 게 아니라 (제작사로부터) 선택받는 입장이다. 10년 동안 ‘이번에도 같이 했으면 좋겠다’는 얘기를 듣는 게 감사하다”며 “매 공연, 매 시즌을 마지막인 것처럼 열심히 해나가겠다”고 했다.'
    test_texts = [test_start, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content

