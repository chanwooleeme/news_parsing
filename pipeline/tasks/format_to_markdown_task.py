#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from logger import get_logger

logger = get_logger(__name__)

def format_article_to_markdown(article: dict) -> str:
    """하나의 뉴스 기사를 이쁘게 문서용 마크다운으로 변환"""
    headline = article.get('headline', '')
    summary_bullets = article.get('summary_bullets', [])
    background = article.get('background', '')
    event_detail = article.get('event_detail', '')
    market_reaction = article.get('market_reaction', '')
    future_implication = article.get('future_implication', '')
    economic_principle_explanation = article.get('economic_principle_explanation', '')

    sections = [
        f"# 📰 {headline}\n",
        f"## 📌 요약",
        "\n".join(f"- {bullet}" for bullet in summary_bullets),
        f"\n## 🧠 배경\n{background}",
        f"\n## 🔎 세부 사항\n{event_detail}",
        f"\n## 📊 시장 반응\n{market_reaction}",
        f"\n## 🚀 향후 전망\n{future_implication}",
        f"\n## 📚 경제 원리 설명\n{economic_principle_explanation}",
    ]

    markdown = "\n\n".join(sections)
    return markdown.strip()

def format_to_markdown(input_file_path: str, output_file_path: str):
    """
    카드 리포트를 마크다운 형식으로 변환
    
    Args:
        input_file_path (str): 카드 리포트가 포함된 JSON 파일 경로
        output_file_path (str): 마크다운으로 변환된 결과를 저장할 파일 경로
        
    Returns:
        str: 출력 파일 경로
    """
    logger.info("🔄 카드 리포트 마크다운 변환 시작")
    
    try:
        # 입력 파일 로드
        with open(input_file_path, 'r', encoding='utf-8') as f:
            card_reports = json.load(f)
        
        # 각 카드 리포트를 마크다운으로 변환
        markdowns = []
        for article in card_reports:
            markdown = format_article_to_markdown(article)
            markdowns.append(markdown)
        
        # 모든 마크다운 합치기
        merged_markdown = "\n\n\n" + "\n\n\n".join(markdowns)
        
        # 출력 파일 저장
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(merged_markdown)
        
        logger.info(f"✅ 마크다운 변환 완료: {len(markdowns)}개 기사")
        return output_file_path
        
    except Exception as e:
        logger.error(f"❌ 마크다운 변환 실패: {str(e)}")
        raise 