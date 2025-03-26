from .base_parser import BaseParser
import re
import json
from typing import Tuple
from datetime import datetime

class ChosunParser(BaseParser):
    def __init__(self, html: str):
        super().__init__(html)
        self._processed_data = None  # Fusion 데이터 캐싱

    def get_author(self) -> str:
        """BaseParser의 get_author 오버라이드"""
        processed = self._process_fusion_data()
        return self._clean_author(processed[1])

    def get_content(self) -> str:
        """BaseParser의 get_content 오버라이드"""
        processed = self._process_fusion_data()
        return self._clean_body(processed[0])

    def get_publication_date(self) -> str:
        iso_str = self.extract_meta("article:published_time")
        iso_str = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_str)
        unix_timestamp = dt.timestamp()  # 초 단위 timestamp
        return unix_timestamp
    

    def _process_fusion_data(self) -> Tuple[str, str]:
        """Fusion 데이터 처리 (캐싱 포함)"""
        if self._processed_data is None:
            script_text = self._find_fusion_script()
            self._processed_data = self._parse_fusion_script(script_text)
        return self._processed_data

    def _find_fusion_script(self) -> str:
        """Fusion.globalContent 스크립트 찾기"""
        for tag in self.soup.find_all(True):
            # 태그 이름
            tag_name = tag.name
            # 속성이 있다면 사전형으로 반환 (없으면 빈 dict)
            attributes = tag.attrs
            # 텍스트 일부 (좌우 공백 제거 후 최대 30자)
            text_snippet = tag.get_text(strip=True)
            if (tag_name == "script" or "sc₩ript") and attributes == {'id': 'fusion-metadata', 'type': 'application/javascript'}:
                return text_snippet

    def _parse_fusion_script(self, script_text: str) -> Tuple[str, str]:
        """스크립트 파싱 및 데이터 추출"""
        match = re.search(r'Fusion\.globalContent\s*=\s*({.*?});', script_text, re.DOTALL)
        if not match:
            return ("", "")
        
        try:
            data = json.loads(match.group(1))
            content = self._extract_article_content(data)
            author = self._extract_raw_author(data)
            return (content, author)
        except json.JSONDecodeError:
            return ("", "")

    def _extract_article_content(self, data: dict) -> str:
        """본문 내용 추출"""
        body_parts = [
            el["content"].strip()
            for el in data.get("content_elements", [])
            if el.get("type") == "text" and "content" in el
        ]
        return " ".join(body_parts)

    def _extract_raw_author(self, data: dict) -> str:
        """원시 작성자 정보 추출"""
        by_list = data.get("credits", {}).get("by", [])
        return by_list[0].get("name", "") if by_list else ""

    def _clean_author(self, author: str) -> str:
        """작성자 이름 정제 (기자, 괄호 내용 제거)"""
        author = re.sub(r'\s*기자\s*\([^)]*\)', '', author)
        return super().clean_author(author).strip()

    def _clean_body(self, text: str) -> str:
        """본문 정제 (🌎 마커 이후 내용 제거)"""
        return re.split(r'\s*-\s*🌎', text, maxsplit=1)[0].strip()
