import pytest
from parser.pressian_parser import PressianParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/프레시안/43220428ddf144e619fa2ea363c37d61.html', 'r', encoding='utf-8') as file:
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
    assert title == "'200년된 법' 끄집어낸 트럼프, 법원 명령 무시하고 베네수엘라 이민자 추방"


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "김효진"

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
    test_start = '도널드 트럼프 미국 행정부가 법원의 제동 명령에도 베네수엘라 이민자 수백 명의 추방을 단행해 법원 결정을 무시했다는 비판을 피할 수 없'
    test_middle = '체 뉴욕시민자유연맹(NYCLU) 사무총장 도나 리버먼은 CNN에 칼릴 추방 시도는 "법적 근거가 없다"며 칼릴이 "(정부 관점에서) 잘못된 정치 사상을 갖고'
    test_end = '등 "일주일 전만 해도 당연하게 여겨졌던 활동들"에 대한 학생들의 질문이 쏟아지고 있다고 전했다.'
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
    
    print(content)