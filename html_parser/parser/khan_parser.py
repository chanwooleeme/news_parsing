from .base_parser import BaseParser
from datetime import datetime
import re

class KhanParser(BaseParser):
    
    def get_title(self) -> str:
        # 우선 og:title meta 태그에서 제목 추출
        title = self.extract_meta("og:title")
        if title:
            return title
        # fallback: <title> 태그 사용
        title_tag = self.soup.find("title")
        if title_tag:
            return self.clean_text(title_tag.get_text())
        return ''
    
    def get_author(self) -> str:
        # article:author meta 태그를 우선 사용
        author = self.extract_meta("article:author")
        if author:
            return author
        # fallback: meta name="author" 태그 사용
        return self.extract_meta("author")

    def get_publication_date(self) -> str:
        # article:published_time meta 태그에서 발행일 추출
        iso_str = self.extract_meta("article:published_time")
        dt = datetime.fromisoformat(iso_str)
        unix_timestamp = dt.timestamp()  # 초 단위 timestamp
        return unix_timestamp
    
    def get_content(self) -> str:
        # 클래스 속성에 "content"가 포함된 모든 <p> 태그 찾기
        p_tags = self.soup.find_all("p", class_=re.compile("content"))
        # 각 태그의 텍스트 추출 후, 줄바꿈 문자로 결합
        all_content = "\n".join(p.get_text(strip=True) for p in p_tags)
        return all_content