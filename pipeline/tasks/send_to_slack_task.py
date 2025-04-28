#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
from logger import get_logger

logger = get_logger(__name__)

def send_to_slack(card_reports_path: str, report_url: str):
    """
    카드 리포트의 헤드라인을 슬랙으로 전송
    
    Args:
        card_reports_path (str): 카드 리포트가 저장된 JSON 파일 경로
        report_url (str): 전체 리포트 URL
        
    Returns:
        bool: 전송 성공 여부
    """
    logger.info("🔄 슬랙 전송 시작")
    
    try:
        # 환경 변수 가져오기
        SLACK_TOKEN = os.getenv("SLACK_TOKEN")
        CHANNEL_ID = os.getenv("CHANNEL_ID")
        
        if not SLACK_TOKEN or not CHANNEL_ID:
            logger.error("❌ 슬랙 토큰 또는 채널 ID가 설정되지 않았습니다.")
            return False
        
        # 카드 리포트 로드
        with open(card_reports_path, 'r', encoding='utf-8') as f:
            card_reports = json.load(f)
        
        # 헤드라인 추출
        headlines = [article.get('headline', '') for article in card_reports]
        
        # 슬랙 메시지 구성
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {SLACK_TOKEN}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        headlines_text = "\n".join(f"- {headline}" for headline in headlines)
        message = f"*오늘의 뉴스 요약*\n\n{headlines_text}\n\n👉 [전체 뉴스 보러가기]({report_url})"
        
        payload = {
            "channel": CHANNEL_ID,
            "text": message,
            "mrkdwn": True
        }
        
        # 슬랙 API 호출
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200 or not response.json().get('ok'):
            logger.error(f"❌ 슬랙 전송 실패: {response.text}")
            return False
        else:
            logger.info("✅ 슬랙 전송 성공!")
            return True
            
    except Exception as e:
        logger.error(f"❌ 슬랙 전송 중 오류 발생: {str(e)}")
        raise 