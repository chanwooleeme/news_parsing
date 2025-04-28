# 1. 시스템 프롬프트 (강화된 단일 라인 + 마커 포함)
REPORT_CARD_STYLE_PROMPT = """
당신은 경제 초보자를 위한 카드뉴스 스타일의 경제 리포트를 작성하는 전문 에디터입니다.

[요청사항]
- 쉽고 친근한 말투 사용 (~입니다, ~했는데요)
- 헤드라인 15자 이내, 본문 3~5줄 단락
- 이모지·수치(%) 강조
- **출력은 반드시 단일 라인 순수 JSON**만 (<JSON>…</JSON> 사이)
- 모든 값은 string 혹은 string 배열 타입이어야 합니다

[구성요소]
1. headline  
   - 15자 이내

2. summary_bullets  
   - 3개 내외

3. background  
   - 3~4문장  
   - 한글 300~350자 내외  

4. event_detail  
   - 4~5문장  
   - 한글 400~450자 내외  

5. market_reaction  

6. future_implication  

7. economic_principle_explanation  

[JSON 출력 규칙]
출력은 `<JSON>`과 `</JSON>` 사이에 있는 단일 라인 JSON만 사용하세요.  
예시:  
<JSON>{"headline":"트럼프, 관세 인하 시사","summary_bullets":["📉 관세 인하 가능성","🤔 중국 반발","📈 증시 반등"],"background":"트럼프 대통령이 대중국 관세 재조정 가능성을 언급했습니다.","event_detail":"23일 트럼프 대통령은 '2~3주 안에 관세율 재조정'을 말했다. 중국은 협상 사실을 부인했습니다.","market_reaction":"다우 1.07%↑, 나스닥 2.5%↑, 금값 3.7%↓","future_implication":"미중 협상 결과에 따라 글로벌 변동성 커질 전망입니다.","economic_principle_explanation":"관세가 낮아지면 수입품 가격이 내려가 소비가 늘어 주식시장도 활기를 띱니다."}</JSON>
""".strip()

def create_card_style_prompt(article_content: str) -> str:
    few_shot = """
[스타일 예시]
<JSON>{"headline":"트럼프, 관세 인하 시사","summary_bullets":["📉 관세 인하 가능성","🤔 중국 반발","📈 증시 반등"],
"background":"트럼프 대통령이 대중국 관세 재조정 가능성을 언급했습니다. 
최근 발표된 수치에 따르면 수출 의존도가 높은 반도체 업계가 민감하게 반응하고 있는데요. 
이는 글로벌 공급망 재편 움직임과도 맞물려 있습니다.","event_detail":"23일 트럼프 대통령은 '2~3주 안에 관세율 재조정'을 말했다. 
회의에 동석한 고위 관계자들은 실무 검토단을 즉시 구성하기로 했습니다. 
중국 상무부는 협상 사실을 공식 부인했으나, 업계에서는 추가 논의가 불가피하다고 보고 있습니다. 
투자자들은 발표 직후 옵션 시장을 중심으로 포지션을 조정했습니다.","market_reaction":"다우 1.07%↑, 나스닥 2.5%↑, 금값 3.7%↓",
"future_implication":"미중 협상 결과에 따라 글로벌 변동성 커질 전망입니다.","economic_principle_explanation":"관세가 낮아지면 수입품 가격이 내려가 소비가 늘어 주식시장도 활기를 띱니다."}</JSON>
(위 예시처럼 background는 300자 이상, event_detail은 400자 이상으로 작성하세요.)
""".strip()

    return f"""
{REPORT_CARD_STYLE_PROMPT}

{few_shot}

[기사 본문]
{article_content}

위에서 제시한 `<JSON>…</JSON>` 형식의 단일 라인 JSON만 출력하세요.
""".strip()


# 3. CardReportGenerator 클래스
from typing import List, Dict
import json
from clients.openai_batcher import OpenAIBatcher
from agentic_retriever.config.models import ModelName

class CardReportGenerator:
    def __init__(self, openai_client, model: ModelName = ModelName.GPT_4O_MINI):
        self.batcher = OpenAIBatcher(openai_client, model=model)

    def generate_card_reports(self, articles: List[Dict]) -> List[Dict]:
        if not articles:
            return []

        prompts = [
            create_card_style_prompt(article['content'])
            for article in articles
        ]

        try:
            responses = self.batcher.batch_chat_completion(
                prompts=prompts,
                system_prompt=REPORT_CARD_STYLE_PROMPT
            )
        except Exception as e:
            print(f"Error calling batch_chat_completion: {e}")
            return []

        results = []
        for i, resp in enumerate(responses):
            article = articles[i]
            article_id = article.get('id')
            text = resp.strip()
            # 마커 기반으로 JSON 추출
            if "<JSON>" in text and "</JSON>" in text:
                start = text.index("<JSON>") + len("<JSON>")
                end = text.index("</JSON>")
                json_str = text[start:end].strip()
            else:
                json_str = text

            try:
                report = json.loads(json_str)
                report['id'] = article_id
                results.append(report)
            except Exception as e:
                print(f"Error parsing JSON for article {article_id}: {e}\nRaw: {json_str}")

        return results
