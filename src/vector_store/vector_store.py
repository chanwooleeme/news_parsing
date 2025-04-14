from typing import List, Dict, Tuple
from src.clients.vector_store import VectorStore
from qdrant_client.models import Filter, FieldCondition, MatchAny

class NewsVectorStore:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def insert(self, vector: List[float], metadata: Dict[str, str]) -> str:
        return self.vector_store.insert(vector, metadata)

    def batch_insert(self, vectors_and_metadata: List[Tuple[List[float], Dict[str, str]]]) -> List[str]:
        return self.vector_store.batch_insert(vectors_and_metadata)

    def search_by_economic_variables(self, economic_variables: List[str], top_k: int = 10) -> List[Dict]:
        """
        경제 변수 필터 기반 검색
        """
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
