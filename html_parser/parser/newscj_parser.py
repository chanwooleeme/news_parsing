from .base_parser import BaseParser
import re

class NewscjParser(BaseParser):
    
    def get_author(self) -> str:
        # article:author meta 태그를 우선 사용
        author = self.extract_meta("dable:author")
        if author:
            return self.clean_author(author)
        return ''
    
    def get_content(self) -> str:
        """기사 본문 추출"""
        # 모든 <p> 태그 선택
        paragraphs = self.soup.find_all('p')
        
        if not paragraphs:
            return ""

        # 본문 내용 수집
        content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        
        # 연속된 공백 및 개행 정리
        content = re.sub(r'\s+', ' ', content)
        
        return self.clean_text(content)