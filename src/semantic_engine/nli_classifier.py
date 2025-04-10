from common.openai_client import get_openai_client
from common.logger import get_logger
from typing import List, Dict, Tuple, Any
import tiktoken
import json
import re

logger = get_logger(__name__)

class NLIClassifier:
    def __init__(self):
        self.client = get_openai_client()
        self.logger = get_logger(__name__)
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        
        # 이건 "형식 지시"만 주는 거야
        self.prompt_template = """
**엄격한 응답 형식 요청**
반드시 다음 구조로만 응답해야 합니다:
{
    "relationship": "연관성 없음|부분 연관|동일 사건|인과 관계|반대 의견",
    "confidence": 0.0~1.0 숫자만,
    "explanation": "20자 이내 요약"
}

주의사항:
- JSON 이외의 텍스트 절대 포함 금지
- 키 이름 변경 불가
- 설명은 간결하게
"""

    def _count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def _optimize_batch_size(self, texts: List[str], max_tokens: int = 4000) -> int:
        total_tokens = sum(self._count_tokens(text) for text in texts)
        if total_tokens == 0:
            return 1
        return min(len(texts), max(1, max_tokens // (total_tokens // len(texts))))

    def _parse_response(self, response_text: str) -> Dict:
        # JSON 형식 강제 정규화
        normalized = re.sub(r'[\n\t]', '', response_text)
        normalized = re.sub(r'\s{2,}', ' ', normalized)
        
        try:
            clean_json = re.search(r'\{.*\}', normalized).group()
            result = json.loads(clean_json)
            return self._validate_output(result)
        except:
            return self._get_default_result()

    def _validate_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["relationship", "confidence", "explanation"]
        if not all(field in result for field in required_fields):
            return self._get_default_result()

        if result["relationship"] not in ["연관성 없음", "부분 연관", "동일 사건", "인과 관계", "반대 의견"]:
            return self._get_default_result()

        try:
            confidence = float(result["confidence"])
            if not 0.0 <= confidence <= 1.0:
                return self._get_default_result()
        except (ValueError, TypeError):
            return self._get_default_result()

        return result

    def _get_default_result(self) -> Dict[str, Any]:
        return {
            "relationship": "연관성 없음",
            "confidence": 0.0,
            "explanation": "분류 실패"
        }

    def classify_relationship(self, article1: str, article2: str) -> Dict[str, Any]:
        try:
            # ✅ 여기 수정! (article1, article2 넣은 user prompt 따로 생성)
            user_prompt = f"""
[기사1]
{article1}

[기사2]
{article2}

{self.prompt_template}
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "너는 두 뉴스 기사 간의 관계를 반드시 JSON 형식으로만 응답해야 한다."},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content

            result = self._parse_response(result_text)
            self.logger.debug(f"파싱 결과: {result}")
            return result
        
        except Exception as e:
            self.logger.error(f"API 호출 또는 파싱 중 오류 발생: {str(e)}")
            return self._get_default_result()

    def classify_relationships_batch(self, new_article: str, existing_articles: List[str]) -> List[Dict[str, Any]]:
        try:
            results = []
            for article in existing_articles:
                try:
                    result = self.classify_relationship(new_article, article)
                    results.append(result)
                    self.logger.info(f"진행 중: {len(results)}/{len(existing_articles)} 완료")
                except Exception as e:
                    self.logger.error(f"관계 분류 실패: {str(e)}")
                    results.append(self._get_default_result())
            return results
        except Exception as e:
            self.logger.error(f"배치 분류 실패: {str(e)}")
            return [self._get_default_result()] * len(existing_articles)
