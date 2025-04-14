# /agentic_retriever/evaluator/sufficiency_checker.py

from typing import List, Tuple

class SufficiencyChecker:
    def __init__(self, gpt_client):
        self.gpt = gpt_client
        self.experts = [
            {
                "name": "비관적 전문가",
                "persona": (
                    "당신은 경제 리스크를 민감하게 평가하는 비관적 경제 전문가입니다. "
                    "정보가 조금만 부족해도 부족하다고 판단합니다."
                )
            },
            {
                "name": "낙관적 전문가",
                "persona": (
                    "당신은 경제 성장 가능성을 긍정적으로 바라보는 낙관적 경제 전문가입니다. "
                    "웬만한 정보가 있으면 충분하다고 판단합니다."
                )
            },
            {
                "name": "중립적 전문가",
                "persona": (
                    "당신은 균형 잡힌 시각을 가진 중립적 경제 분석가입니다. "
                    "객관적으로 정보의 충분성을 신중히 평가합니다."
                )
            }
        ]

    def check_sufficiency(self, summary: str) -> Tuple[bool, List[str]]:
        """
        전문가 3명에게 sufficiency 평가 요청
        :param summary: 최종 요약 텍스트
        :return: (부족 여부, 전문가별 평가 리스트)
        """
        decisions = []

        for expert in self.experts:
            prompt = (
                f"{expert['persona']}\n\n"
                "아래 경제 뉴스 요약을 보고, 리포트를 작성하기에 충분한 정보가 있는지 평가하세요.\n"
                "충분하면 'YES', 부족하면 'NO'로만 답하십시오.\n\n"
                f"요약 내용:\n{summary}"
            )
            response = self.gpt.chat_completion(prompt)
            decision = response.strip().upper()
            decisions.append(decision)

        no_count = decisions.count("NO")
        is_insufficient = no_count >= 2  # 3명 중 2명 이상이 NO면 부족
        return is_insufficient, decisions
