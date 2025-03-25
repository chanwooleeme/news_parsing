import pytest
from parser.seoul_parser import SeoulParser as Parser
from datetime import datetime
from datetime import timezone
import os

@pytest.fixture
def sample_html():
    with open('html/서울신문/e45bae4d4ab8b5171931d94bd9dcb53d.html', 'rb') as file:
        content = file.read()
    
    # 에러 무시하고 디코딩 ('replace'는 잘못된 문자를 ''로 대체)
    return content.decode('utf-8', errors='replace')

    # 또는 더 엄격하게 처리하고 싶다면:
    # return content.decode('utf-8', errors='ignore')  # 잘못된 문자를 무시

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
    assert title == '[단독] 또 제주항공… 정비 결함으로 발 묶였다'


def test_get_author(sample_html):
    """작성자 파싱 테스트"""
    parser = Parser(sample_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "손지연"

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
    print(content)
    test_start = '제주항공 항공기가 기체 정비 문제로 인도네시아 발리국제공항에서 18시간 넘게 발이 묶였다가 결국 취소됐다. 무안 제'
    test_middle = '객들은 두 차례나 정비 결함이 발견돼 두려움에 밤을 지새워야 했다. 임신 19주차인 최모(32)씨는 “같은 항공기에서 두 차례나 결함'
    test_end = '제주항공은 지난 4일에도 기체 날개 결함으로 인해 김포에서 제주로 향하던 여객기가 회항하기도 했다.'
    test_texts = [test_start, test_middle, test_end]
    assert content != ""
    assert isinstance(content, str)
    for test_text in test_texts:
        assert test_text in content
