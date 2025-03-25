import pytest
from parser.khan_parser import KhanParser
from datetime import datetime
from bs4 import BeautifulSoup

@pytest.fixture
def sample_khan_html():
    with open('html/경향신문/4a11d97d7fda1a45c8b213fb462a841a.html', 'r', encoding='utf-8') as file:
        return file.read()

def get_publication_date(iso_str: str) -> str:
    # article:published_time meta 태그에서 발행일 추출
    dt = datetime.fromisoformat(iso_str)
    unix_timestamp = dt.timestamp()  # 초 단위 timestamp
    return unix_timestamp
    

def test_get_title(sample_khan_html):
    """제목 파싱 테스트"""
    parser = KhanParser(sample_khan_html)
    title = parser.get_title()
    assert title != ""
    assert isinstance(title, str)
    # 실제 예상되는 제목으로 테스트
    assert title == "윤 대통령 형사 재판 두번째 준비기일…직접 출석은 안해"


def test_get_author(sample_khan_html):
    """작성자 파싱 테스트"""
    parser = KhanParser(sample_khan_html)
    author = parser.get_author()
    assert author != ""
    assert isinstance(author, str)
    assert author == "이예슬 기자"

def test_get_publication_date(sample_khan_html):
    """발행 날짜 파싱 테스트"""
    parser = KhanParser(sample_khan_html)
    publication_date = parser.get_publication_date()
    assert publication_date != ""
    assert isinstance(publication_date, float)
    assert publication_date == 1742769420.0

def test_get_content(sample_khan_html):
    """본문 파싱 테스트"""
    parser = KhanParser(sample_khan_html)
    content = parser.get_content()
    test_text = '김 전 장관 등과 공모해 위헌·위법한 비상계엄을 선포하는 등 국헌 문란을 목적으로 폭동을 일으킨 혐의 등으로 기소됐다.'
    assert content != ""
    assert isinstance(content, str)
    assert test_text in content


@pytest.mark.parametrize('file_path,expected_data', [
    ('4a11d97d7fda1a45c8b213fb462a841a.html', {
        'title': "윤 대통령 형사 재판 두번째 준비기일…직접 출석은 안해",
        'author': "이예슬 기자",
        'content_snippet': "김 전 장관 등과 공모해 위헌·위법한 비상계엄을 선포하는 등 국헌 문란을 목적으로 폭동을 일으킨 혐의 등으로 기소됐다."
    }),
    ('9639c4aff9f4cfa3d05b15d24722797c.html', {
        'title': "살처분 산란계 수, '살처분 요건 완화'에도 큰 폭 증가",
        'author': "안광호 기자",  # 실제 작성자로 변경 필요
        'content_snippet': "(8067만마리) 사육 마리의 약 4.6%로, 수급에 미치는 영향은 극히 낮다”고 말했다."  # 실제 본문 일부로 변경 필요
    }),
    ('d9ae08085715140ca24012d869119bda.html', {
        'title': "'용산 출신 국악원장' 반발에…유인촌 \"국악인 80% 반대하면 따르겠다\"",
        'author': "신주영 기자",  # 실제 작성자로 변경 필요
        'content_snippet': " 공연 극장인 국립극장과 예술의전당은 산하에 예술단체를 두지 않고 외부 예술단체에 공연장을 대관하는 방식"  # 실제 본문 일부로 변경 필요
    }),
])
def test_various_articles_full(file_path, expected_data):
    """여러 기사의 모든 요소 테스트"""
    with open(f'html/경향신문/{file_path}', 'r', encoding='utf-8') as file:
        html = file.read()
    parser = KhanParser(html)
    
    
    # 작성자 테스트
    author = parser.get_author()
    assert author == expected_data['author']
    
    
    # 본문 테스트
    content = parser.get_content()
    assert expected_data['content_snippet'] in content

    # 기본 검증
    assert all([
        isinstance(author, str),
        isinstance(content, str)
    ])