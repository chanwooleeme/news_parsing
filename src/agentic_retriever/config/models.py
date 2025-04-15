from enum import Enum

class ModelName(Enum):
    GPT_4O = ("gpt-4o", 128000, False)
    GPT_4O_MINI = ("gpt-4o-mini", 128000, False)
    TEXT_EMBEDDING_3_LARGE = ("text-embedding-3-large", 8191, True)

    def __init__(self, model_name: str, max_input_tokens: int, is_embedding: bool):
        self._model_name = model_name
        self._max_input_tokens = max_input_tokens
        self._is_embedding = is_embedding

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def max_tokens(self) -> int:
        """세이프티 마진 200 토큰 기본 반영"""
        return self._max_input_tokens - 200

    @property
    def is_embedding_model(self) -> bool:
        return self._is_embedding
