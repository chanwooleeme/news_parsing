# /agentic_retriever/aggregator/report_aggregator.py

from clients.openai_batcher import OpenAIBatcher
from agentic_retriever.config.models import ModelName
from agentic_retriever.prompts.report_aggregator_prompt import (
    REPORT_AGGREGATOR_SYSTEM_PROMPT,
    REPORT_AGGREGATOR_USER_PROMPT_TEMPLATE,
)

class ReportAggregator:
    def __init__(self, openai_client, model: ModelName = ModelName.GPT_4O):
        self.batcher = OpenAIBatcher(openai_client, model=model)

    def generate_final_report(self, final_summary: str) -> str:
        """최종 요약을 기반으로 깔끔한 경제 리포트 생성"""
        user_prompt = REPORT_AGGREGATOR_USER_PROMPT_TEMPLATE.format(summary=final_summary)

        responses = self.batcher.batch_chat_completion(
            prompts=[user_prompt],
            system_prompt=REPORT_AGGREGATOR_SYSTEM_PROMPT,
        )

        final_report = responses[0].strip()
        return final_report
