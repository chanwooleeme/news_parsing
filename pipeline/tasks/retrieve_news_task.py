#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from logger import get_logger
from utils.config import BASE_API_URL, call_api
from typing import List

logger = get_logger(__name__)

API_URL = BASE_API_URL + "/search-articles"
    
def retrieve_news(temp_file_path: str) -> str:
    """
    뉴스 API에서 기사를 검색하고 결과를 임시 파일에 저장
    
    Args:
        temp_file_path (str): 검색 결과를 저장할 임시 파일 경로
        
    Returns:
        str: 저장된 파일 경로
    """
    logger.info(f"📰 뉴스 데이터 조회 시작: {API_URL}")
    
    try:
        # API 호출
        response = call_api(API_URL)
        
        if not response or 'results' not in response:
            logger.error("❌ API 응답이 유효하지 않습니다.")
            raise ValueError("API 응답이 유효하지 않습니다.")
        
        articles = response['results']
        logger.info(f"✅ 뉴스 데이터 조회 완료: {len(articles)}개 기사")
        
        # 임시 파일에 저장
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 뉴스 데이터 파일 저장 완료: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        logger.error(f"❌ 뉴스 데이터 조회 또는 저장 실패: {str(e)}")
        raise
