# /agentic_retriever/retriever/missing_info_analyzer.py

from typing import List

class MissingInfoAnalyzer:
    def __init__(self, gpt_client):
        self.gpt = gpt_client

    def analyze_missing_info(self, summary: str) -> List[str]:
        """
        요약을 기반으로 부족한 정보를 추출
        :param summary: 최종 요약 텍스트
        :return: 부족한 키워드 리스트
        """
        prompt = (
            "당신은 경제 뉴스 분석 전문가입니다.\n"
            "아래 경제 뉴스 요약을 검토하고, 리포트를 작성하는 데 필요한데 현재 빠져 있는 주요 주제나 정보가 무엇인지 분석하세요.\n"
            "간단한 키워드 목록(예: '금리', '환율', '원자재', '고용지표') 형태로만 답하십시오.\n\n"
            f"{summary}"
        )

        response = self.gpt.chat_completion(prompt)

        # 결과를 키워드 리스트로 변환
        keywords = [line.strip("-• ").strip() for line in response.strip().splitlines() if line.strip()]
        return keywords
