# retriever/retriever.py

from typing import List, Dict, Optional
from common.qdrant_client import get_qdrant_client
from indexer.embedder import NewsEmbedder
from qdrant_client.http.models import Filter, FieldCondition, MatchText

class NewsRetriever:
    def __init__(self, collection_name: str = "news-articles", embedder: Optional[NewsEmbedder] = None):
        self.collection_name = collection_name
        self.qdrant = get_qdrant_client()
        self.embedder = embedder or NewsEmbedder()  # 외부 주입 없으면 디폴트

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, str]] = None) -> List[Dict]:
        embedding = self.embedder.embed_text(query)
        qdrant_filter = self._build_filter(filters) if filters else None

        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=top_k,
            query_filter=qdrant_filter
        )

        results = response.points

        return [
            {
                "score": r.score,
                "title": r.payload.get("title", ""),
                "newspaper": r.payload.get("newspaper", ""),
                "category": r.payload.get("category", ""),
                "timestamp": r.payload.get("timestamp", ""),
                "content": r.payload.get("content", "")[:300]
            }
            for r in results
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
