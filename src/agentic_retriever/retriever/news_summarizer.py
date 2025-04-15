from typing import List, Dict
from clients.openai_batcher import OpenAIBatcher
from agentic_retriever.config.models import ModelName
from agentic_retriever.prompts.news_summarizer_prompt import (
    NEWS_SUMMARIZER_SYSTEM_PROMPT,
    NEWS_SUMMARIZER_USER_PROMPT_TEMPLATE,
)

class NewsSummarizer:
    def __init__(self, openai_client, model: ModelName=ModelName.GPT_4O_MINI):
        self.batcher = OpenAIBatcher(openai_client, model=model)

    def summarize_batches(self, articles: List[Dict]) -> List[str]:
        """Batch별로 요약해서 partial summaries 반환"""
        partial_summaries = []

        # 1. 기사 -> 프롬프트 변환
        prompts = []
        for idx, article in enumerate(articles):
            title = article.get("title", "")
            content = article.get("content", "")
            prompts.append(f"{idx+1}. 제목: {title}\n본문: {content[:500]}...\n")

        # 2. batching
        batched_prompts = self.batcher.batch_chat_completion(prompts)

        # 3. batch 별로 chat_completion
        for batch in batched_prompts:
            user_prompt = NEWS_SUMMARIZER_USER_PROMPT_TEMPLATE.format(articles="\n".join(batch))
            responses = self.batcher.batch_chat_completion(
                prompts=[user_prompt],
                system_prompt=NEWS_SUMMARIZER_SYSTEM_PROMPT,
            )

            # 4. 응답 저장
            summary = responses[0]
            partial_summaries.append(summary.strip())

        return partial_summaries