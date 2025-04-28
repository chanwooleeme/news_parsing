#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from agentic_retriever.evaluator.sufficiency_checker import SufficiencyChecker
from agentic_retriever.config.models import ModelName
from typing import List
from utils.config import BASE_API_URL
import requests
from utils.client import get_openai_client
from logger import get_logger

logger = get_logger(__name__)

def update_importance(point_id, importance):
    """API를 통해 기사의 중요도 업데이트"""
    url = BASE_API_URL + "/update-article-importance"
    requests.post(url, json={"point_id": point_id, "importance": importance})
    logger.info(f"✅ 중요도 업데이트 완료: {point_id} -> {importance}")

def check_sufficient(input_file_path: str, output_file_path: str) -> str:
    """
    기사의 충분성을 평가하고 충분히 중요한 기사만 추출
    
    Args:
        input_file_path (str): 검색된 기사가 저장된 JSON 파일 경로
        output_file_path (str): 충분성 평가 결과를 저장할 JSON 파일 경로
        
    Returns:
        str: 저장된 파일 경로
    """
    logger.info("🔄 기사 충분성 평가 시작")
    
    try:
        # 입력 파일 로드
        with open(input_file_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        # OpenAI 클라이언트 초기화
        openai_client = get_openai_client()
        
        # 충분성 평가
        checker = SufficiencyChecker(openai_client, model=ModelName.GPT_4O_MINI)
        sufficiency_result = checker.check_sufficiency(articles)
        
        # 중요한 기사만 추출
        sufficient_summaries = []
        for result in sufficiency_result:
            importance = int(result['importance'])
            if importance >= 3:
                sufficient_summaries.append({
                    "id": result['id'],
                    "importance": importance,
                    "content": result['content']
                })
            # API를 통해 기사 중요도 업데이트
            update_importance(result['id'], importance)
        
        logger.info(f"✅ 충분성 평가 완료: {len(sufficient_summaries)}/{len(sufficiency_result)}개 선택됨")
        
        # 결과 파일 저장
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(sufficient_summaries, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 충분성 평가 결과 저장 완료: {output_file_path}")
        return output_file_path
        
    except Exception as e:
        logger.error(f"❌ 충분성 평가 또는 저장 실패: {str(e)}")
        raise
