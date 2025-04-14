import tiktoken
from typing import List
from logger import get_logger

logger = get_logger(__name__)

class NewsEmbedding:
    def __init__(self, openai_client, model_name="text-embedding-3-large"):
        self._client = openai_client
        self.model_name = model_name
        self.encoding = tiktoken.encoding_for_model(model_name)
        self.max_tokens = 8191  # OpenAI API의 최대 입력 토큰 수
    
    def set_client(self, openai_client, model_name="text-embedding-3-large"):
        self._client = openai_client
        self.model_name = model_name
        self.encoding = tiktoken.encoding_for_model(model_name)

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
        if not self._client:
            raise RuntimeError("Client must be set before embedding")
            
        try:
            return self._client.embed_text(text, self.model_name)
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트를 배치로 임베딩"""
        if not self._client:
            raise RuntimeError("Client must be set before embedding")
            
        all_embeddings = []
        
        # 토큰 수를 고려하여 최적의 배치로 나눔
        batches = self._optimize_batch_size(texts)
        logger.info(f"총 {len(batches)}개 배치로 나눔")
        
        for i, batch in enumerate(batches):
            try:
                # 배치 임베딩 API 호출
                response = self._client.embeddings.create(
                    input=batch,
                    model=self.model_name
                )
                # 응답 객체가 Pydantic 모델이면 dict로 변환
                if hasattr(response, 'dict'):
                    response = response.dict()
                # 응답의 'data' 필드에서 실제 임베딩 벡터 추출
                batch_embeddings = [item["embedding"] for item in response["data"]]
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"배치 {i+1}/{len(batches)} 임베딩 완료 (토큰 수: {sum(self._count_tokens(text) for text in batch)})")
            except Exception as e:
                logger.error(f"배치 임베딩 실패: {e}")
                # 오류 발생 시, 개별 텍스트에 대해 임베딩 재요청(단일 요청)
                for text in batch:
                    try:
                        single_response = self._client.embeddings.create(
                            input=[text],
                            model=self.model_name
                        )
                        if hasattr(single_response, 'dict'):
                            single_response = single_response.dict()
                        embedding = single_response["data"][0]["embedding"]
                        all_embeddings.append(embedding)
                    except Exception as inner_e:
                        logger.error(f"개별 임베딩 실패: {inner_e}")
                        # 에러 발생 시 빈 임베딩 (예외 상황 처리)
                        all_embeddings.append([])
        
        return all_embeddings
