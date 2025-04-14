# /agentic_retriever/retriever/summary_aggregator.py

from typing import List

class SummaryAggregator:
    def __init__(self, gpt_client, model_max_tokens: int = 3896):
        self.gpt = gpt_client
        self.model_max_tokens = model_max_tokens

    def aggregate_summaries(self, partial_summaries: List[str]) -> str:
        """여러 partial 요약을 하나의 최종 요약으로 정리"""
        combined_text = "\n\n".join(partial_summaries)

        prompt = (
            "당신은 경제 뉴스 요약 전문가입니다.\n"
            "아래에 여러 개의 경제 뉴스 요약이 주어집니다.\n"
            "이 중복되거나 겹치는 내용을 제거하고, 핵심만 남겨 하나의 통합된 경제 리포트를 작성하세요.\n"
            "- 중요한 경제 흐름, 투자 정보, 시장 동향을 중심으로 구성하십시오.\n"
            "- 불필요한 세부사항은 생략하십시오.\n"
            "- 깔끔하고 구조화된 3~5문단 요약을 작성하십시오.\n\n"
            f"{combined_text}"
        )

        final_summary = self.gpt.chat_completion(prompt)
        return final_summary.strip()
