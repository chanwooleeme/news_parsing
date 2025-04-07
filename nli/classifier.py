# nli/classifier.py

from common.openai_client import get_openai_client
from common.logger import get_logger

logger = get_logger(__name__)

class NLIClassifier:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.client = get_openai_client()
        self.model_name = model_name

    def classify_relationship(self, new_article: str, existing_article: str) -> str:
        """
        새 기사와 기존 기사 간의 관계를 분류
        (포함/변경/확장/모순/무관)
        """
        prompt = f"""
너는 뉴스 기사 간의 사실 비교를 수행하는 전문가야.

[새 기사]
{new_article}

[기존 기사]
{existing_article}

두 기사 간의 관계를 아래 중 하나로 분류하고, 이유를 간단히 설명해줘.

선택지:
- 포함
- 변경
- 확장
- 모순
- 무관

형식: <관계>: <간단한 이유>
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"NLI 분류 실패: {e}")
            raise
