import tiktoken
from typing import List
from common.openai_client import get_openai_client
from common.logger import get_logger

logger = get_logger(__name__)

class NewsEmbedder:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.openai_client = get_openai_client()
        self.encoding = tiktoken.encoding_for_model(model_name)
        self.max_tokens = 8191  # OpenAI API의 최대 입력 토큰 수

    def _count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수를 계산"""
        return len(self.encoding.encode(text))

    def _optimize_batch_size(self, texts: List[str], max_tokens: int = 8191) -> List[List[str]]:
        """토큰 수를 고려하여 최적의 배치 크기로 나눔"""
        batches = []
        current_batch = []
        current_tokens = 0

        for text in texts:
            text_tokens = self._count_tokens(text)
            
            # 현재 배치에 추가할 수 있는지 확인
            if current_tokens + text_tokens <= max_tokens:
                current_batch.append(text)
                current_tokens += text_tokens
            else:
                # 현재 배치가 비어있지 않으면 저장
                if current_batch:
                    batches.append(current_batch)
                # 새로운 배치 시작
                current_batch = [text]
                current_tokens = text_tokens

        # 마지막 배치 추가
        if current_batch:
            batches.append(current_batch)

        return batches

    def embed_text(self, text: str) -> List[float]:
        """단일 텍스트 임베딩"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.model_name
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트를 배치로 임베딩"""
        all_embeddings = []
        
        # 토큰 수를 고려하여 최적의 배치로 나눔
        batches = self._optimize_batch_size(texts)
        logger.info(f"총 {len(batches)}개 배치로 나눔")
        
        for i, batch in enumerate(batches):
            try:
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model=self.model_name
                )
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                logger.info(f"배치 {i+1}/{len(batches)} 임베딩 완료 (토큰 수: {sum(self._count_tokens(text) for text in batch)})")
            except Exception as e:
                logger.error(f"배치 임베딩 실패: {e}")
                # 오류 발생 시 개별 처리로 폴백
                for text in batch:
                    try:
                        embedding = self.embed_text(text)
                        all_embeddings.append(embedding)
                    except Exception as inner_e:
                        logger.error(f"개별 임베딩 실패: {inner_e}")
                        # 빈 임베딩으로 대체
                        all_embeddings.append([])
        
        return all_embeddings
    