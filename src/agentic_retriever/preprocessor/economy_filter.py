from typing import List, Dict
from agentic_retriever.config.models import ModelName
from openai import OpenAI
from agentic_retriever.prompts.economy_filter_prompt import ECONOMY_FILTER_SYSTEM_PROMPT, ECONOMY_FILTER_USER_PROMPT_TEMPLATE
from clients.openai_batcher import OpenAIBatcher

class EconomyFilter:
    def __init__(self, openai_client: OpenAI, model: ModelName = ModelName.GPT_4O_MINI):
        self.batcher = OpenAIBatcher(openai_client, model=model)

    def filter_economy_articles(self, articles: List[Dict]) -> List[Dict]:
        """경제 관련 뉴스만 필터링"""
        economy_articles = []

        # 기사별 프롬프트 생성
        prompts = []
        index_map = []
        for idx, article in enumerate(articles):
            title = article.get("title", "")
            content = article.get("content", "")
            prompt = f"{idx+1}. 제목: {title}\n본문: {content[:500]}...\n"
            prompts.append(prompt)
            index_map.append(idx)

        # 하나로 합쳐 GPT에 질문
        combined_prompt = "\n".join(prompts)
        user_prompt = ECONOMY_FILTER_USER_PROMPT_TEMPLATE.format(articles=combined_prompt)

        responses = self.batcher.batch_chat_completion(
            prompts=[user_prompt],
            system_prompt=ECONOMY_FILTER_SYSTEM_PROMPT,
        )

        # 응답 처리
        response = responses[0]
        lines = response.strip().splitlines()
        print(lines)
        for i, line in enumerate(lines):
            answer = line.strip().upper()
            if "YES" in answer and i < len(index_map):
                economy_articles.append(articles[index_map[i]])

        return economy_articles

if __name__ == "__main__":
    import openai
    import os
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    economy_filter = EconomyFilter(openai_client, model=ModelName.GPT_4O_MINI)
    articles = [
        {"title": "삼성전자, 반도체 실적 호조", "content": "삼성전자는 올해 1분기 반도체 부문 실적이 기대치를 웃돌았다고 밝혔다..."},
        {"title": "방탄소년단, 월드투어 성료", "content": "BTS는 LA에서 마지막 콘서트를 열고 월드투어를 마무리했다..."},
        {"title": "한은 기준금리 동결", "content": "한국은행은 기준금리를 현재 수준인 3.5%로 동결하기로 결정했다..."},
    ]

    economy_articles = economy_filter.filter_economy_articles(articles)
    print(economy_articles)