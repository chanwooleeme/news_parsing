import tiktoken
from logger import get_logger
from openai import OpenAI
from agentic_retriever.config.models import ModelName
from typing import List

logger = get_logger(__name__)

class OpenAIBatcher:
    def __init__(self, openai_client: OpenAI, model: ModelName, max_tokens=128000, margin=2000):
        self.client = openai_client
        self.model = model
        self.max_tokens = max_tokens
        self.margin = margin
        self.encoding = tiktoken.encoding_for_model(self.model.name)
        logger.info(f"🔄 OpenAIBatcher 초기화 완료 (model: {model.name}, max_tokens: {max_tokens}, margin: {margin})")

    def _count_tokens(self, text: str) -> int:
        token_count = len(self.encoding.encode(text))
        logger.debug(f"📊 토큰 수 계산: {token_count} tokens")
        return token_count

    def _smart_split(self, text: str) -> List[str]:
        """긴 텍스트를 토큰 한도에 맞게 분할"""
        logger.info("✂️ 텍스트 분할 시작")
        lines = text.split('\n')
        batches, current_batch, current_tokens = [], [], 0

        for line in lines:
            line_tokens = self._count_tokens(line)
            if current_tokens + line_tokens > (self.max_tokens - self.margin):
                batches.append("\n".join(current_batch))
                current_batch, current_tokens = [], 0
            current_batch.append(line)
            current_tokens += line_tokens

        if current_batch:
            batches.append("\n".join(current_batch))

        logger.info(f"✅ 텍스트 분할 완료: {len(batches)} 배치 생성")
        return batches

    def _optimize_batch_size(self, texts: List[str]) -> List[List[str]]:
        """토큰 수를 고려하여 최적의 배치 크기로 나눔"""
        batches, current_batch, current_tokens = [], [], 0
        for text in texts:
            token_count = self._count_tokens(text)
            if current_tokens + token_count <= (self.max_tokens - self.margin):
                current_batch.append(text)
                current_tokens += token_count
            else:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [text]
                current_tokens = token_count
        if current_batch:
            batches.append(current_batch)
        return batches

    def batch_chat_completion(self, prompts: List[str], system_prompt: str = "") -> List[str]:
        """배치로 ChatCompletion 요청 (토큰 초과시 smart split 포함)"""
        logger.info(f"🔄 배치 처리 시작: {len(prompts)} 개의 프롬프트")
        all_responses = []

        for i, prompt in enumerate(prompts):
            token_count = self._count_tokens(prompt)
            if token_count > (self.max_tokens - self.margin):
                logger.warning(f"⚠️ 프롬프트 {i+1} 토큰 초과 ({token_count} tokens). smart split 진행")
                for part in self._smart_split(prompt):
                    all_responses.append(self._single_chat_completion(part, system_prompt))
            else:
                all_responses.append(self._single_chat_completion(prompt, system_prompt))

        logger.info(f"✅ 배치 처리 완료: {len(all_responses)} 개의 응답 생성")
        return all_responses

    def _single_chat_completion(self, prompt: str, system_prompt: str) -> str:
        """개별 ChatCompletion 호출"""
        logger.debug("🔄 OpenAI Chat API 호출 시작")
        response = self.client.chat.completions.create(
            model=self.model.name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """배치로 임베딩 처리"""
        if not self.model.is_embedding_model:
            raise ValueError(f"❌ 현재 모델({self.model.name})은 임베딩 전용이 아닙니다.")

        logger.info(f"🔄 임베딩 시작: {len(texts)} 개 텍스트")
        all_embeddings = []

        # batch optimize
        batches = self._optimize_batch_size(texts)
        logger.info(f"📦 총 {len(batches)}개 배치로 분할됨")

        for i, batch in enumerate(batches):
            try:
                response = self.client.embeddings.create(
                    model=self.model.name,
                    input=batch
                )
                embeddings = [item["embedding"] for item in response.data]
                all_embeddings.extend(embeddings)
                logger.info(f"✅ 배치 {i+1}/{len(batches)} 처리 완료")
            except Exception as e:
                logger.warning(f"⚠️ 배치 {i+1} 실패 → 개별 임베딩 시도: {e}")
                for text in batch:
                    try:
                        response = self.client.embeddings.create(
                            model=self.model.name,
                            input=[text]
                        )
                        embedding = response.data[0]["embedding"]
                        all_embeddings.append(embedding)
                    except Exception as inner_e:
                        logger.error(f"❌ 단일 임베딩 실패: {inner_e}")
                        all_embeddings.append([])  # fallback: 빈 벡터

        return all_embeddings
