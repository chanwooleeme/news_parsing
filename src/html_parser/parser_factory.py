from logger import get_logger
import os
import sys
from typing import Dict, Type, Any

logger = get_logger("parser_factory")

from .parser.base_parser import BaseParser
from .parser.chosun_parser import ChosunParser
from .parser.newscj_parser import NewscjParser
from .parser.pressian_parser import PressianParser
from .parser.womennews_parser import WomennewsParser
from .parser.ablenews_parser import AblenewsParser
from .parser.sisajournal_parser import SisajournalParser
from .parser.segye_parser import SegyeParser
from .parser.seoul_parser import SeoulParser
from .parser.mediatoday_parser import MediatodayParser
from .parser.donga_parser import DongaParser
from .parser.labortoday_parser import LabortodayParser
from .parser.khan_parser import KhanParser
from .parser.newsis_parser import NewsisParser


class ParserFactory:
    """
    신문사별 HTML 파서 팩토리
    신문사 이름을 기준으로 적절한 파서를 선택하고 parse() 메서드로 결과 반환
    """
    
    def __init__(self):
        """파서 팩토리 초기화 - 신문사 이름과 파서 클래스 매핑"""
        self.parsers: Dict[str, Type[BaseParser]] = {
            '조선일보': ChosunParser,
            '천지일보': NewscjParser,
            '프레시안': PressianParser,
            '여성신문': WomennewsParser,
            '에이블뉴스': AblenewsParser,
            '시사저널': SisajournalParser,
            '세계일보': SegyeParser,
            '서울신문': SeoulParser,
            '미디어오늘': MediatodayParser,
            '동아일보': DongaParser,
            '매일노동뉴스': LabortodayParser,
            '경향신문': KhanParser,
            '뉴시스': NewsisParser
        }
        
        logger.info(f"ParserFactory initialized with {len(self.parsers)} parsers")
    
    def parse(self, html: str, newspaper: str) -> Dict[str, Any]:
        """
        신문사 이름으로 파서를 선택하고 기사 정보를 파싱하여 반환
        
        Args:
            html: 파싱할 HTML 문자열
            newspaper: 신문사 이름
            
        Returns:
            파싱된 기사 정보 딕셔너리
            {
                'title': 기사 제목,
                'author': 작성자,
                'category': 카테고리,
                'publication_date': 발행일 (타임스탬프),
                'content': 본문 내용
            }
            
        Raises:
            ValueError: 지원하지 않는 신문사인 경우
        """
        if newspaper not in self.parsers:
            available_parsers = ', '.join(self.parsers.keys())
            error_msg = f"신문사 '{newspaper}'에 대한 파서가 없습니다. 지원되는 신문사: {available_parsers}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        parser_class = self.parsers[newspaper]
        logger.info(f"신문사 '{newspaper}'에 {parser_class.__name__} 파서 사용")
        
        try:
            parser = parser_class(html)
            result = parser.parse()  # BaseParser의 parse() 메서드 활용
            logger.info(f"파싱 완료: {newspaper} 기사 - '{result.get('title', '')[:30]}...'")
            return result
        except Exception as e:
            logger.error(f"파싱 중 오류 발생: {e}")
            raise

    def get_supported_newspapers(self) -> list:
        """지원되는 신문사 목록 반환"""
        return list(self.parsers.keys())