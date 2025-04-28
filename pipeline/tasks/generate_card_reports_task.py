#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from logger import get_logger
from report_generator.card_report_generator import CardReportGenerator
from utils.client import get_openai_client

logger = get_logger(__name__)

def generate_card_reports(input_file_path: str, output_file_path: str, max_reports: int = 5):
    """
    충분한 데이터를 가진 기사들로부터 카드 리포트 생성
    
    Args:
        input_file_path (str): 충분한 기사들이 포함된 JSON 파일 경로
        output_file_path (str): 생성된 카드 리포트를 저장할 JSON 파일 경로
        max_reports (int): 생성할 최대 리포트 수
    
    Returns:
        str: 출력 파일 경로
    """
    logger.info(f"🔄 카드 리포트 생성 시작 (최대 {max_reports}개)")
    
    try:
        # 입력 파일 로드
        with open(input_file_path, 'r', encoding='utf-8') as f:
            sufficient_summaries = json.load(f)
        
        # 중요도 순으로 정렬
        sufficient_summaries.sort(key=lambda x: x.get('importance', 0), reverse=True)
        sufficient_summaries = sufficient_summaries[:max_reports]
        
        # OpenAI 클라이언트 초기화
        openai_client = get_openai_client()
        
        # 카드 리포트 생성
        card_report_generator = CardReportGenerator(openai_client)
        card_reports = card_report_generator.generate_card_reports(sufficient_summaries)
        
        # 헤드라인 정리
        for article in card_reports:
            article['headline'] = article.get('headline', '').replace('"', '')
        
        # 출력 파일 저장
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(card_reports, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 카드 리포트 생성 완료: {len(card_reports)}개")
        return output_file_path
    
    except Exception as e:
        logger.error(f"❌ 카드 리포트 생성 실패: {str(e)}")
        raise 