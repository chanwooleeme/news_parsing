from common.openai_client import get_openai_client
from common.logger import get_logger
from typing import List

logger = get_logger(__name__)


class NewsEmbedder:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.openai_client = get_openai_client()
        self.model_name = model_name

    def embed_text(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            input=text,
            model=self.model_name
        )
        return response.data[0].embedding
    