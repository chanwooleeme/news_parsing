# /dags/daily_economy_report_dag.py

from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import timedelta
import os
import json
from datetime import datetime
from logger import get_logger

from tasks.retrieve_news_task import retrieve_news_task
from tasks.check_sufficient_task import check_sufficient_task
from report_generator.card_report_generator import CardReportGenerator
logger = get_logger(__name__)

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

import requests

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

def save_markdown_file(markdown_text: str, filename: str):
    """Markdown 파일로 저장"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    print(f"✅ Markdown 저장 완료: {filename}")

def send_headlines_to_slack(headlines, markdown_url, slack_token, channel):
    """Slack에 헤드라인 리스트와 전체보기 링크 전송"""
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    headlines_text = "\n".join(f"- {headline}" for headline in headlines)
    message = f"*오늘의 뉴스 요약*\n\n{headlines_text}\n\n👉 [전체 뉴스 보러가기]({markdown_url})"

    payload = {
        "channel": channel,
        "text": message,
        "mrkdwn": True
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200 or not response.json().get('ok'):
        print(f"❌ Slack 전송 실패: {response.text}")
    else:
        print(f"✅ Slack 전송 성공!")

with DAG(
    dag_id='daily_economy_report_dag',
    default_args=default_args,
    start_date=days_ago(1), 
    schedule_interval="0 0 * * *",  # UTC 0시 (KST 9시)
    catchup=False,
    tags=['news', 'report'],
) as dag:

    @task
    def generate_and_send_report():
        from utils.client import get_openai_client
        openai_client = get_openai_client()
        SLACK_TOKEN = os.getenv("SLACK_TOKEN")
        CHANNEL_ID = os.getenv("CHANNEL_ID")
        logger.info("🔄 경제 리포트 생성 프로세스 시작")
        articles = retrieve_news_task()
        logger.info("📊 컨텍스트 충분성 평가 시작")
        sufficient_summaries = check_sufficient_task(articles, openai_client)

        sufficient_summaries.sort(key=lambda x: x['importance'], reverse=True)
        sufficient_summaries = sufficient_summaries[:5]
        card_report_generator = CardReportGenerator(openai_client)
        card_reports = card_report_generator.generate_card_reports(sufficient_summaries)
        headlines = []
        markdowns = []
        for article in card_reports:
            article['headline'] = article['headline'].replace('"', '')
            headlines.append(article['headline'])
            markdown = format_article_to_markdown(article)
            markdowns.append(markdown)
        merged_markdown = "\n\n\n" + "\n\n\n".join(markdowns)

        save_markdown_file(merged_markdown, "daily_economy_report.md")
        send_headlines_to_slack(headlines, "https://tmp.com", SLACK_TOKEN, CHANNEL_ID)        

    generate_and_send_report()
