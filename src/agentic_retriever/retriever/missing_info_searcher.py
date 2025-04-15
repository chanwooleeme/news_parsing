# /agentic_retriever/searcher/missing_info_searcher.py

from typing import List, Dict
from vector_store.vector_store import NewsVectorStore

class MissingInfoSearcher:
    def __init__(self, news_vector_store: NewsVectorStore):
        self.news_vector_store = news_vector_store

    def search_missing_info(self, missing_keywords: List[str], top_k: int = 10) -> List[Dict]:
        """부족한 키워드로 Qdrant 검색"""
        if not missing_keywords:
            return []

        articles = self.news_vector_store.search_by_economic_variables(
            economic_variables=missing_keywords,
            top_k=top_k,
        )
        return articles
