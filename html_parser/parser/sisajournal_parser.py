from .base_parser import BaseParser
import re
import logging
from typing import Optional

class SisajournalParser(BaseParser):
    """시사저널 웹사이트 HTML 파서"""

    def get_title(self) -> str:
        title = super().get_title()
        title = title.replace(" - 시사저널", "").strip()
        return title
    
    def get_author(self) -> str:
        """시사저널 기사 작성자 파싱"""
        try:
            # 방법 1: meta 태그에서 작성자 확인
            author = self.extract_meta("article:author") or self.extract_meta("author")
            if author:
                return self.clean_author(author)
            
            # 방법 2: CSS 선택자로 작성자 정보 찾기
            author_elem = self.soup.select_one('.writer, .byline')
            if author_elem:
                return self.clean_author(author_elem.get_text(strip=True))
                
            # 방법 3: 본문 내 첫 단락에서 작성자 패턴 찾기
            first_p = self.soup.select_one('#article_content p:first-child')
            if first_p and '기자' in first_p.get_text():
                author_match = re.search(r'([가-힣]+)\s*기자', first_p.get_text())
                if author_match:
                    return author_match.group(1)
            
            return ""
        except Exception as e:
            logging.error(f"시사저널 작성자 파싱 중 오류 발생: {e}")
            return ""
    
    def clean_author(self, author: str) -> str:
        return author.split(' ')[0]
    
    def get_content(self) -> str:
        """
        시사저널 기사 본문 파싱
        CSS 선택자를 사용하여 본문 내용을 추출
        """
        try:
            # CSS 선택자를 사용하여 기사 본문 컨테이너 선택
            article_content = self.soup.select_one('#article_content')
            
            if not article_content:
                logging.warning("시사저널 기사에서 본문 컨테이너를 찾을 수 없습니다")
                return ""
            
            # 불필요한 요소 제거: 이미지 캡션, 광고, 소스 등
            for caption in article_content.select('.caption, .ad_box, .source'):
                if caption:
                    caption.decompose()
            
            # 단락 텍스트 추출 및 결합
            paragraphs = [p.get_text(strip=True) for p in article_content.select('p') if p.get_text(strip=True)]
            
            if not paragraphs:
                # 대안: 전체 컨테이너 텍스트 사용
                return self.clean_text(article_content.get_text())
                
            content = ' '.join(paragraphs)
            return self.clean_text(content)
        except Exception as e:
            logging.error(f"시사저널 기사 본문 파싱 중 오류 발생: {e}")
            return ""