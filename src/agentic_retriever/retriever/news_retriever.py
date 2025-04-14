# /agentic_retriever/retriever/news_retriever.py

from typing import List, Dict, Optional
from datetime import datetime, timedelta

class NewsRetriever:
    def __init__(self):
        self._client = None
        self.collection_name = None
    
    def set_client(self, client, collection_name):
        self._client = client
        self.collection_name = collection_name

    def retrieve(
        self,
        economic_variables: List[str],
        recent_days: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """경제 변수 기반으로 최근 N일 내 뉴스 검색"""
        if not self._client or not self.collection_name:
            raise RuntimeError("Client and collection name must be set before retrieval")
            
        # 클라이언트에 의존하는 로직은 pipeline에서 구현
        return self._client.retrieve_news(
            collection_name=self.collection_name,
            economic_variables=economic_variables,
            recent_days=recent_days,
            limit=limit
        )
