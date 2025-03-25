from .base_parser import BaseParser
from datetime import datetime
import re

class KhanParser(BaseParser):
    
    def get_content(self) -> str:
        # 클래스 속성에 "content"가 포함된 모든 <p> 태그 찾기
        p_tags = self.soup.find_all("p", class_=re.compile("content"))
        # 각 태그의 텍스트 추출 후, 줄바꿈 문자로 결합
        all_content = " ".join(p.get_text(strip=True) for p in p_tags)
        return all_content