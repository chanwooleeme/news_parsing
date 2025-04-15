# /agentic_retriever/analyzer/missing_info_analyzer.py

from typing import List
from clients.openai_batcher import OpenAIBatcher
from agentic_retriever.config.models import ModelName
from agentic_retriever.prompts.missing_info_analyzer_prompt import (
    MISSING_INFO_SYSTEM_PROMPT,
    MISSING_INFO_USER_PROMPT_TEMPLATE,
)

class MissingInfoAnalyzer:
    def __init__(self, openai_client, model: ModelName = ModelName.GPT_4O):
        self.batcher = OpenAIBatcher(openai_client, model=model)

    def analyze_missing_info(self, summary: str) -> List[str]:
        """요약을 기반으로 부족한 키워드 추출"""
        user_prompt = MISSING_INFO_USER_PROMPT_TEMPLATE.format(summary=summary)

        responses = self.batcher.batch_chat_completion(
            prompts=[user_prompt],
            system_prompt=MISSING_INFO_SYSTEM_PROMPT,
        )

        keywords = []
        if responses:
            lines = responses[0].strip().splitlines()
            for line in lines:
                keyword = line.strip("-• ").strip()
                if keyword:
                    keywords.append(keyword)

        return keywords
