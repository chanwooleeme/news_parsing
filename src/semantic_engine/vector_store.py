# src/vector_store/vector_store.py

from typing import List, Dict, Optional
import uuid
from common.qdrant_client import get_qdrant_client
from qdrant_client.http.models import Filter, FieldCondition, MatchText, PointStruct

class QdrantVectorStore:
    def __init__(self, collection_name: str = "news-articles", qdrant_client: QdrantClient = None):
        self.collection_name = collection_name
        self.qdrant = qdrant_client if qdrant_client else get_qdrant_client()

    def save(self, vector: List[float], metadata: Dict[str, str]) -> str:
        """
        외부에서 생성한 임베딩 벡터를 Qdrant에 저장
        """
        point_id = str(uuid.uuid4())

        payload = metadata.copy()

        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        return point_id

    def retrieve(self, query_vector: List[float], top_k: int = 5, filters: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        외부에서 생성한 쿼리 임베딩 벡터로 검색
        """
        qdrant_filter = self._build_filter(filters) if filters else None

        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter
        )

        return [
            {
                "score": r.score,
                "payload": r.payload
            }
            for r in response.points
        ]

    def _build_filter(self, filters: Dict[str, str]) -> Filter:
        return Filter(
            must=[
                FieldCondition(
                    key=key,
                    match=MatchText(text=value)
                )
                for key, value in filters.items()
            ]
        )
