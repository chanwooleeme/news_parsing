# /agentic_retriever/preprocessor/economy_filter.py

from typing import List, Dict

class EconomyFilter:
    def __init__(self, gpt_client, max_input_tokens: int = 3800):
        self.gpt = gpt_client
        self.max_input_tokens = max_input_tokens

    def _estimate_tokens(self, text: str) -> int:
        """텍스트 길이로 대충 토큰 수 추정"""
        return len(text) // 4

    def _smart_batch(self, articles: List[Dict]) -> List[List[Dict]]:
        """토큰 최적화 기준으로 batch 나누기"""
        batches = []
        current_batch = []
        current_tokens = 0

        for article in articles:
            title = article.get("title", "")
            content = article.get("content", "")
            estimated_tokens = self._estimate_tokens(title) + self._estimate_tokens(content)

            # batch 끊을 타이밍
            if current_tokens + estimated_tokens > self.max_input_tokens:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(article)
            current_tokens += estimated_tokens

        if current_batch:
            batches.append(current_batch)

        return batches

    def _make_batch_prompt(self, batch: List[Dict]) -> str:
        prompts = []
        for idx, article in enumerate(batch):
            title = article.get("title", "")
            content = article.get("content", "")
            prompts.append(f"{idx+1}. 제목: {title}\n본문: {content[:500]}...\n")
        
        batch_text = "\n".join(prompts)
        
        return (
            "당신은 뉴스 분류 전문가입니다.\n"
            "아래에 여러 뉴스 기사들이 제공됩니다.\n"
            "각 뉴스에 대해 '경제 관련' 여부를 판단하십시오.\n"
            "각 번호별로 'YES' 또는 'NO'로만 답하십시오.\n\n"
            f"{batch_text}"
        )

    def filter_economy_articles(self, articles: List[Dict]) -> List[Dict]:
        """경제 관련 뉴스만 batch로 걸러내기"""
        economy_articles = []
        batches = self._smart_batch(articles)

        for batch in batches:
            prompt = self._make_batch_prompt(batch)
            response = self.gpt.chat_completion(prompt)

            lines = response.strip().splitlines()
            for idx, line in enumerate(lines):
                answer = line.strip().upper()
                if idx < len(batch) and answer == "YES":
                    economy_articles.append(batch[idx])

        return economy_articles
