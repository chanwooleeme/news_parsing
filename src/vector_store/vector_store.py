from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from clients.vector_store import VectorStore
from qdrant_client.models import Filter, FieldCondition, MatchAny, Range

class NewsVectorStore:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def insert(self, vector: List[float], metadata: Dict[str, str]) -> str:
        return self.vector_store.insert(vector, metadata)

    def batch_insert(self, vectors_and_metadata: List[Tuple[List[float], Dict[str, str]]]) -> List[str]:
        return self.vector_store.batch_insert(vectors_and_metadata)

    def retrieve_today_news(self, top_k: int = 10) -> List[Dict]:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        tomorrow_start = today_start + timedelta(days=1)

        query_filter = Filter(
            must=[
                FieldCondition(
                    key="publication_date",
                    range=Range(
                        gte=int(today_start.timestamp()),
                        lt=int(tomorrow_start.timestamp())
                    )
                )
            ]
        )

        results = self.vector_store.search(
            query_vector=None,
            top_k=top_k,
            query_filter=query_filter
        )

        return [point["payload"] for point in results]
    
    def search_by_economic_variables(self, economic_variables: List[str], top_k: int = 10) -> List[Dict]:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="economic_variables",
                    match=MatchAny(any=economic_variables)
                )
            ]
        )

        results = self.vector_store.search(
            query_vector=None,
            top_k=top_k,
            query_filter=query_filter
        )

        articles = []
        for point in results:
            payload = point["payload"]
            articles.append({
                "title": payload.get("title", ""),
                "content": payload.get("content", ""),
                "economic_variables": payload.get("economic_variables", []),
                "publication_date": payload.get("publication_date")
            })

        return articles

    def retrieve_news(
        self,
        economic_variables: List[str],
        recent_days: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """경제 변수 + 최근 날짜 조건까지 필터해서 뉴스 검색"""
        must_conditions = []

        if economic_variables:
            must_conditions.append(
                FieldCondition(
                    key="economic_variables",
                    match=MatchAny(any=economic_variables)
                )
            )

        if recent_days is not None:
            now_ts = int(datetime.utcnow().timestamp())
            start_ts = now_ts - (recent_days * 86400)  # 초 단위
            must_conditions.append(
                FieldCondition(
                    key="publication_date",
                    range=Range(gte=start_ts)
                )
            )

        query_filter = Filter(must=must_conditions)

        results = self.vector_store.search(
            query_vector=None,
            top_k=limit,
            query_filter=query_filter
        )

        return [point["payload"] for point in results]
