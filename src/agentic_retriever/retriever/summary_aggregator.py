# /agentic_retriever/retriever/summary_aggregator.py

from typing import List
from clients.openai_batcher import OpenAIBatcher
from agentic_retriever.config.models import ModelName
from agentic_retriever.prompts.summary_aggregator_prompt import (
    SUMMARY_AGGREGATOR_SYSTEM_PROMPT,
    SUMMARY_AGGREGATOR_USER_PROMPT_TEMPLATE,
)

class SummaryAggregator:
    def __init__(self, openai_client, model: ModelName):
        self.batcher = OpenAIBatcher(openai_client, model=model)

    def aggregate_summaries(self, partial_summaries: List[str]) -> str:
        """여러 partial 요약을 하나로 통합"""
        if not partial_summaries:
            return ""

        # 1. partial summaries 연결
        combined_text = "\n\n".join(partial_summaries)

        # 2. user prompt 생성
        user_prompt = SUMMARY_AGGREGATOR_USER_PROMPT_TEMPLATE.format(partials=combined_text)

        # 3. chat completion 호출
        responses = self.batcher.batch_chat_completion(
            prompts=[user_prompt],
            system_prompt=SUMMARY_AGGREGATOR_SYSTEM_PROMPT,
        )

        # 4. 최종 하나의 요약 반환
        final_summary = responses[0].strip()
        return final_summary
