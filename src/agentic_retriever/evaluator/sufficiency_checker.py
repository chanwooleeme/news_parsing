# /agentic_retriever/evaluator/sufficiency_checker.py

from typing import List, Tuple
from clients.openai_batcher import OpenAIBatcher
from agentic_retriever.config.models import ModelName
from agentic_retriever.prompts.sufficiency_checker_prompt import (
    SUFFICIENCY_SYSTEM_PROMPT,
    SUFFICIENCY_USER_PROMPT_TEMPLATE,
)

class SufficiencyChecker:
    def __init__(self, openai_client, model: ModelName=ModelName.GPT_4O_MINI):
        self.batcher = OpenAIBatcher(openai_client, model=model)
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
        전문가 3명 sufficiency 평가 요청
        :param summary: 최종 요약 텍스트
        :return: (부족 여부, 전문가별 평가 리스트)
        """
        # 1. 전문가별 프롬프트 생성
        prompts = []
        for expert in self.experts:
            user_prompt = SUFFICIENCY_USER_PROMPT_TEMPLATE.format(
                persona=expert["persona"],
                summary=summary
            )
            prompts.append(user_prompt)

        # 2. batch chat_completion 호출
        responses = self.batcher.batch_chat_completion(
            prompts=prompts,
            system_prompt=SUFFICIENCY_SYSTEM_PROMPT,
        )

        decisions = [resp.strip().upper() for resp in responses]

        # 3. 최종 sufficiency 판정
        no_count = decisions.count("NO")
        is_insufficient = no_count >= 2  # 3명 중 2명이 NO면 부족
        return is_insufficient, decisions
