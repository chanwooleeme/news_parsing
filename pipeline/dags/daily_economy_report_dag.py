# /dags/daily_economy_report_dag.py

from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import timedelta
import os
import json
from datetime import datetime
from logger import get_logger

from agentic_retriever.preprocessor.economy_filter import EconomyFilter
from agentic_retriever.retriever.news_summarizer import NewsSummarizer
from agentic_retriever.retriever.summary_aggregator import SummaryAggregator
from agentic_retriever.evaluator.sufficiency_checker import SufficiencyChecker
from agentic_retriever.retriever.missing_info_analyzer import MissingInfoAnalyzer
from agentic_retriever.retriever.missing_info_searcher import MissingInfoSearcher
from agentic_retriever.report_generator.report_aggregator import ReportAggregator
from agentic_retriever.config.models import ModelName
from vector_store.vector_store import NewsVectorStore
from clients.qdrant_vector_store import QdrantVectorStore
from clients.slack_client import SlackClient

logger = get_logger(__name__)

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def save_test_data(data, step_name, data_type="json"):
    """테스트용 데이터를 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = "/opt/airflow/data/test_outputs"
    os.makedirs(save_dir, exist_ok=True)
    
    filename = f"{save_dir}/{step_name}_{timestamp}"
    
    if data_type == "json":
        with open(f"{filename}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        with open(f"{filename}.txt", "w", encoding="utf-8") as f:
            f.write(str(data))
    
    logger.info(f"💾 테스트 데이터 저장: {step_name} -> {filename}")

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
        from utils.client import get_openai_client, get_qdrant_client
        from utils.economy_keyword import get_all_categories

        logger.info("🔄 경제 리포트 생성 프로세스 시작")
        openai_client = get_openai_client()
        qdrant_client = get_qdrant_client()
        collection_name = "economy-articles"
        slack_token = os.getenv("SLACK_TOKEN")
        
        # 1. 뉴스 가져오기
        logger.info("📰 뉴스 데이터 조회 시작")
        vs = QdrantVectorStore(qdrant_client, collection_name=collection_name)
        vector_store = NewsVectorStore(vector_store=vs)
        articles = vector_store.retrieve_news(
            economic_variables=get_all_categories(), recent_days=1, limit=100
        )
        logger.info(f"📊 조회된 뉴스 기사 수: {len(articles)}")
        save_test_data(articles, "raw_articles")

        # 2. 경제 관련 필터링
        logger.info("🔍 경제 관련 기사 필터링 시작")
        economy_filter = EconomyFilter(openai_client, model=ModelName.GPT_4O_MINI)
        economy_articles = economy_filter.filter_economy_articles(articles)
        logger.info(f"📈 경제 관련 기사 수: {len(economy_articles)}")
        save_test_data(economy_articles, "filtered_economy_articles")

        # 3. 뉴스 요약
        logger.info("📝 뉴스 요약 시작")
        summarizer = NewsSummarizer(openai_client, model=ModelName.GPT_4O_MINI)
        partial_summaries = summarizer.summarize_batches(economy_articles)
        logger.info(f"📋 생성된 부분 요약 수: {len(partial_summaries)}")
        save_test_data(partial_summaries, "partial_summaries")

        # 4. 요약 합치기
        logger.info("🔄 요약 통합 시작")
        aggregator = SummaryAggregator(openai_client, model=ModelName.GPT_4O_MINI)
        final_summary = aggregator.aggregate_summaries(partial_summaries)
        logger.info("✅ 요약 통합 완료")
        save_test_data(final_summary, "final_summary", "txt")

        # 5. sufficiency 평가
        logger.info("📊 요약 충분성 평가 시작")
        checker = SufficiencyChecker(openai_client, model=ModelName.GPT_4O)
        is_insufficient, decisions = checker.check_sufficiency(final_summary)
        logger.info(f"📊 충분성 평가 결과: {'부족' if is_insufficient else '충분'}")
        save_test_data({
            "is_insufficient": is_insufficient,
            "decisions": decisions
        }, "sufficiency_check")

        # 6. 부족하면 추가 검색
        if is_insufficient:
            logger.info("🔍 부족한 정보 추가 검색 시작")
            analyzer = MissingInfoAnalyzer(openai_client, model=ModelName.GPT_4O_MINI)
            missing_keywords = analyzer.analyze_missing_info(final_summary)
            logger.info(f"🔑 추가 검색 키워드: {missing_keywords}")
            save_test_data(missing_keywords, "missing_keywords")

            searcher = MissingInfoSearcher(vector_store)
            missing_articles = searcher.search_missing_info(missing_keywords)
            logger.info(f"📰 추가 검색된 기사 수: {len(missing_articles)}")
            save_test_data(missing_articles, "missing_articles")

            # context 확장
            extended_articles = economy_articles + missing_articles
            partial_summaries = summarizer.summarize_batches(extended_articles)
            final_summary = aggregator.aggregate_summaries(partial_summaries)
            logger.info("✅ 추가 정보 통합 완료")
            save_test_data(final_summary, "final_summary_after_extension", "txt")

        # 7. 최종 리포트 생성
        logger.info("📄 최종 리포트 생성 시작")
        report_builder = ReportAggregator(openai_client, model=ModelName.GPT_4O)
        final_report = report_builder.generate_final_report(final_summary)
        logger.info("✅ 최종 리포트 생성 완료")
        save_test_data(final_report, "final_report", "txt")

        # 8. Slack 발송
        logger.info("📤 Slack 발송 시작")
        slack = SlackClient(slack_token)
        slack.send_message(channel="#economy-reports", text=final_report)
        logger.info("✅ Slack 발송 완료")
        logger.info("🎉 경제 리포트 생성 프로세스 완료")

    generate_and_send_report()
