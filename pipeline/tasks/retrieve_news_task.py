#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
from logger import get_logger
from utils.config import BASE_API_URL
from typing import List, Dict, Any

logger = get_logger(__name__)

API_URL = BASE_API_URL + "/search-articles"

def remove_duplicate_contents(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    콘텐츠가 중복된 기사를 제거 (앞 50자 기준으로 중복 체크)
    
    Args:
        articles (List[Dict]): 원본 기사 리스트
        
    Returns:
        List[Dict]: 중복이 제거된 기사 리스트
    """
    unique_articles = {}
    
    for article in articles:
        # 콘텐츠 앞 50자를 키로 사용하여 중복 체크
        content_prefix = article.get('content', '')[:50]
        
        # 중복되지 않았거나, 기존 항목보다 ID가 작은 경우 저장
        if content_prefix not in unique_articles or article['id'] < unique_articles[content_prefix]['id']:
            unique_articles[content_prefix] = article
    
    # 중복 제거된 기사만 리스트로 반환
    result = list(unique_articles.values())
    
    logger.info(f"🔍 중복 제거: {len(articles)}개 -> {len(result)}개")
    return result
    
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
        request_params = {
            "time_range_sec": 60 * 60 * 24,
            "top_k": 10
        }
        response = requests.get(API_URL, params=request_params)

        if response.status_code != 200:
            logger.error(f"❌ API 응답이 유효하지 않습니다. 상태 코드: {response.status_code}")
            raise ValueError("API 응답이 유효하지 않습니다.")
        
        response = response.json()

        if not response or 'results' not in response:
            logger.error("❌ API 응답이 유효하지 않습니다.")
            raise ValueError("API 응답이 유효하지 않습니다.")
        
        articles = response['results']
        logger.info(f"✅ 뉴스 데이터 조회 완료: {len(articles)}개 기사")
        
        # 중복 콘텐츠 제거
        unique_articles = remove_duplicate_contents(articles)
        
        # 임시 파일에 저장
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(unique_articles, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 뉴스 데이터 파일 저장 완료: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        logger.error(f"❌ 뉴스 데이터 조회 또는 저장 실패: {str(e)}")
        raise
