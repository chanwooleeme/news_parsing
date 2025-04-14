# /agentic_retriever/retriever/news_summarizer.py

from typing import List, Dict

class NewsSummarizer:
    def __init__(self, gpt_client, model_max_tokens: int = 3896):
        self.gpt = gpt_client
        self.model_max_tokens = model_max_tokens

    def _estimate_tokens(self, text: str) -> int:
        """텍스트 길이로 대충 토큰 수 추정"""
        return len(text) // 4

    def _smart_batch(self, articles: List[Dict]) -> List[List[Dict]]:
        """토큰 용량 기준으로 batch 나누기"""
        batches = []
        current_batch = []
        current_tokens = 0

        for article in articles:
            title = article.get("title", "")
            content = article.get("content", "")
            estimated_tokens = self._estimate_tokens(title) + self._estimate_tokens(content)

            if current_tokens + estimated_tokens > self.model_max_tokens:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(article)
            current_tokens += estimated_tokens

        if current_batch:
            batches.append(current_batch)

        return batches

    def _make_batch_prompt(self, batch: List[Dict]) -> str:
        """요약용 프롬프트 생성"""
        prompts = []
        for idx, article in enumerate(batch):
            title = article.get("title", "")
            content = article.get("content", "")
            prompts.append(f"{idx+1}. 제목: {title}\n본문: {content[:500]}...\n")

        batch_text = "\n".join(prompts)

        return (
            "당신은 경제 뉴스 요약 전문가입니다.\n"
            "아래 여러 뉴스 기사들을 보고, 경제 관점에서 중요한 내용만 요약하십시오.\n"
            "- 기업 동향, 금리 변화, 환율, 투자, 무역, 산업 트렌드 중심으로 요약하세요.\n"
            "- 중복 없이, 포괄적으로 묶어서 요약하십시오.\n\n"
            f"{batch_text}"
        )

    def summarize_batches(self, articles: List[Dict]) -> List[str]:
        """Batch별로 요약해서 partial summaries 반환"""
        partial_summaries = []
        batches = self._smart_batch(articles)

        for batch in batches:
            prompt = self._make_batch_prompt(batch)
            summary = self.gpt.chat_completion(prompt)
            partial_summaries.append(summary.strip())

        return partial_summaries
