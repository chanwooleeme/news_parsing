# /agentic_retriever/evaluator/sufficiency_checker.py

from typing import List, Dict
from clients.openai_batcher import OpenAIBatcher
from agentic_retriever.config.models import ModelName
import json

# 새로운 프롬프트 정의 (JSON 출력 강제)
REPORT_QUALITY_SYSTEM_PROMPT_JSON = """
당신은 경제 초보자를 위한 일일 경제 보고서를 작성하는 기사 평가 전문가입니다.
다음은 뉴스 기사 하나입니다. 이를 분석하여 아래 기준에 따라 5단계 숫자 등급으로 분류해주세요.

[분류 등급]
1: 매우 부적절 - 경제와 무관하거나, 신뢰성이 낮고 사실 오류가 있는 내용
2: 부적절 - 경제와의 연관성이 약하거나, 영향 예측이 불분명한 사건
3: 보통 - 경제 지표에 간접적 영향을 줄 수 있는 사건 (예: 대기업 신사업 진출 등)
4: 적합 - 특정 산업에 파급 효과가 예상되는 사건 (예: 반도체 수출 규제 등)
5: 매우 적합 - 경제 전반에 중대한 영향을 미치는 사건 (예: 기준금리 인상, 대규모 정책 등)

[평가 기준]
- 핵심 사건의 규모와 파급력
- 경제적 영향에 대한 구체적인 근거 제시 여부
- 초보자 기준의 이해 가능성 (전문 용어 최소화)
- 신뢰 가능한 출처 또는 전문가 인용 포함 여부

[출력 규칙]
● 반드시 다음 형식의 JSON 객체만 출력 (다른 텍스트 금지)

[예시 1 - 매우 적합]
{
  "classification": 5
}

[예시 2 - 보통]
{
  "classification": 3
}

[예시 3 - 매우 부적절]
{
  "classification": 1
}
""".strip()

REPORT_QUALITY_USER_PROMPT_TEMPLATE_JSON = """
[기사 ID]: {article_id}

[본문]:
{article_content}

위 기사에 대해 적합성을 평가하고, 위에서 제시된 형식에 맞는 JSON 객체만 출력해주세요.
다른 텍스트는 포함하지 마세요.
""".strip()

class SufficiencyChecker:
    def __init__(self, openai_client, model: ModelName = ModelName.GPT_4O_MINI):
        self.batcher = OpenAIBatcher(openai_client, model=model)

    def check_sufficiency(self, articles: List[dict]) -> List[dict]:
        if not articles:
            return []

        prompts = []
        for article in articles:
            user_prompt = REPORT_QUALITY_USER_PROMPT_TEMPLATE_JSON.format(
                article_id=article.get('id', 'N/A'),
                article_content=article.get('content', '')
            )
            prompts.append(user_prompt)

        try:
            responses = self.batcher.batch_chat_completion(
                prompts=prompts,
                system_prompt=REPORT_QUALITY_SYSTEM_PROMPT_JSON
            )
        except Exception as e:
            print(f"Error calling batch_chat_completion: {e}")
            # 모두 “매우 부적절”로 간주
            return [
                {
                    'id': a.get('id'),
                    'importance': 1,
                    'content': a.get('content', '')
                }
                for a in articles
            ]

        results = []
        for i, resp_str in enumerate(responses):
            article = articles[i]
            article_id = article.get('id')
            importance = 1

            try:
                clean = resp_str.strip()
                # ```json 블록 제거
                if clean.startswith("```json"):
                    clean = clean[7:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()

                llm_output = json.loads(clean)
                importance = int(llm_output.get("classification", 1))

            except json.JSONDecodeError:
                print(f"Error decoding JSON for article {article_id}: Invalid JSON.\nResponse: {resp_str}")
            except Exception as e:
                print(f"Unexpected error parsing response for article {article_id}: {e}\nResponse: {resp_str}")

            results.append({
                'id': article_id,
                'importance': importance,
                'content': article.get('content', '')
            })

        return results
