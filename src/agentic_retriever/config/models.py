# /agentic_retriever/config/models.py

from enum import Enum

class ModelName(Enum):
    GPT_4O = ("gpt-4o", 4096)
    GPT_4O_MINI = ("gpt-4o-mini", 4096)

    def __init__(self, model_name: str, max_input_tokens: int):
        self._model_name = model_name
        self._max_input_tokens = max_input_tokens

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def max_tokens(self) -> int:
        """세이프티 마진 200 토큰 자동 반영"""
        return self._max_input_tokens - 200  # 기본적으로 200토큰 마진 확보
