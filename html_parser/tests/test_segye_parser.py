import pytest
from parser.segye_parser import SegyeParser as Parser
from datetime import datetime
from datetime import timezone

@pytest.fixture
def sample_html():
    with open('html/세계일보/e4658d145d621119ebeee5610627d4a7.html', 'r', encoding='utf-8') as file:
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
    assert title == '강형욱, 갑질 논란 후 텅빈 정수리 \'충격\'…"13kg 빠지고, 탈모로 병원行"'


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "김지수"

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
    test_start = '반려견 훈련사 강형욱이 갑질 논란에 휘말린 후 스트레스성 탈모에 시달렸다고 고백했다.'
    test_middle = '냥 왔다”며 “세 번째 방문 때는 아내의 손을 잡고 갔다. 너무 쑥스러웠다”고 털어놨다.'
    test_end = '부는 사내 메신저를 무단으로 열람한 혐의로 피소됐으나 경찰은 지난달 무혐의 처분을 내렸다.'
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
    
    print(content)