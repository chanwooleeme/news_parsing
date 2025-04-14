# /agentic_retriever/retriever/missing_info_searcher.py

from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny

class MissingInfoSearcher:
    def __init__(self, qdrant_client: QdrantClient, collection_name: str):
        self.qdrant = qdrant_client
        self.collection_name = collection_name

    def search_missing_info(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """
        부족한 키워드를 기반으로 Qdrant에서 뉴스 검색
        :param keywords: 부족 키워드 리스트
        :param limit: 키워드당 가져올 기사 개수
        :return: 검색된 기사 리스트
        """
        all_results = []

        for keyword in keywords:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="economic_variables",
                        match=MatchAny(any=[keyword])
                    )
                ]
            )

            result = self.qdrant.query_points(
                collection_name=self.collection_name,
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False
            )

            for point in result.points:
                payload = point.payload or {}
                all_results.append({
                    "title": payload.get("title", ""),
                    "content": payload.get("content", ""),
                    "economic_variables": payload.get("economic_variables", []),
                    "publication_date": payload.get("publication_date")
                })

        return all_results
