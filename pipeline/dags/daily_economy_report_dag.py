# /dags/daily_economy_report_dag.py

from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

from agentic_retriever.preprocessor.economy_filter import EconomyFilter
from agentic_retriever.retriever.news_retriever import NewsRetriever
from agentic_retriever.retriever.news_summarizer import NewsSummarizer
from agentic_retriever.retriever.summary_aggregator import SummaryAggregator
from agentic_retriever.evaluator.sufficiency_checker import SufficiencyChecker
from agentic_retriever.retriever.missing_info_analyzer import MissingInfoAnalyzer
from agentic_retriever.retriever.missing_info_searcher import MissingInfoSearcher
from agentic_retriever.report_generator.report_aggregator import ReportAggregator
from agentic_retriever.slack.slack_client import SlackClient
from agentic_retriever.config.models import ModelName


default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

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

        openai_client = get_openai_client()
        qdrant_client = get_qdrant_client()

        gpt_mini_client = openai_client.get_client(model_name=ModelName.GPT_4O_MINI.name)
        gpt_full_client = openai_client.get_client(model_name=ModelName.GPT_4O.name)
        slack_token = os.getenv("SLACK_TOKEN")
        # 1. 뉴스 가져오기
        retriever = NewsRetriever()
        retriever.set_client(qdrant_client, collection_name="economy-articles")
        articles = retriever.retrieve(
            economic_variables=get_all_categories(), recent_days=1, limit=100
        )

        # 2. 경제 관련 필터링
        economy_filter = EconomyFilter(gpt_mini_client)
        economy_articles = economy_filter.filter_economy_articles(articles)

        # 3. 뉴스 요약
        summarizer = NewsSummarizer(gpt_mini_client, model_max_tokens=ModelName.GPT_4O_MINI.max_tokens)
        partial_summaries = summarizer.summarize_batches(economy_articles)

        # 4. 요약 합치기
        aggregator = SummaryAggregator(gpt_mini_client)
        final_summary = aggregator.aggregate_summaries(partial_summaries)

        # 5. sufficiency 평가
        checker = SufficiencyChecker(gpt_full_client)
        is_insufficient, decisions = checker.check_sufficiency(final_summary)

        # 6. 부족하면 추가 검색
        if is_insufficient:
            analyzer = MissingInfoAnalyzer(gpt_mini_client)
            missing_keywords = analyzer.analyze_missing_info(final_summary)

            searcher = MissingInfoSearcher(qdrant_client, collection_name="economy-articles")
            missing_articles = searcher.search_missing_info(missing_keywords)

            # context 확장
            extended_articles = economy_articles + missing_articles
            partial_summaries = summarizer.summarize_batches(extended_articles)
            final_summary = aggregator.aggregate_summaries(partial_summaries)

        # 7. 최종 리포트 생성
        report_builder = ReportAggregator(gpt_full_client)
        final_report = report_builder.generate_final_report(final_summary)

        # 8. Slack 발송
        slack = SlackClient(slack_token)
        slack.send_message(channel="#economy-reports", text=final_report)

    generate_and_send_report()
