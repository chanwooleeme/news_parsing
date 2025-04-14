# /agentic_retriever/report_generator/report_aggregator.py

from typing import List

class ReportAggregator:
    def __init__(self, gpt_client):
        self.gpt = gpt_client

    def generate_final_report(self, summary: str) -> str:
        """
        3명의 전문가가 합의하여 최종 경제 리포트를 작성
        :param summary: 최종 요약 텍스트
        :return: 합의된 최종 리포트 텍스트
        """
        prompt = (
            "당신은 세 명의 경제 전문가입니다.\n"
            "- 전문가 A: 경제 리스크에 민감한 비관적 전문가\n"
            "- 전문가 B: 경제 성장 가능성을 긍정적으로 평가하는 낙관적 전문가\n"
            "- 전문가 C: 객관적이고 균형 잡힌 중립적 전문가\n\n"
            "아래 경제 뉴스 요약을 검토하고, 세 전문가가 각각 다음을 수행하십시오:\n"
            "1. 자신의 관점에서 분석 의견을 작성하십시오.\n"
            "2. 서로 의견을 비교하고 조율하여, 가장 신뢰성 있고 종합적인 최종 경제 리포트를 작성하십시오.\n"
            "3. 리포트는 다음 항목을 포함해야 합니다:\n"
            "- 현재 경제 상황 요약\n"
            "- 주요 리스크 및 기회\n"
            "- 향후 전망\n\n"
            f"경제 뉴스 요약:\n{summary}"
        )

        final_report = self.gpt.chat_completion(prompt)
        return final_report.strip()
