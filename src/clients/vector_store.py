from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any

class VectorStore(ABC):
    @abstractmethod
    def insert(self, vector: List[float], metadata: Optional[Dict[str, str]] = None) -> str:
        """
        하나의 벡터 저장 (ID 반환)
        """
        pass

    @abstractmethod
    def batch_insert(self, vectors_and_metadata: List[Tuple[List[float], Dict[str, str]]]) -> List[str]:
        """
        여러 벡터 저장
        """
        pass

    @abstractmethod
    def search(self, query_vector: Optional[List[float]], top_k: int = 5, query_filter: Optional[Dict[str, Any]] = None) -> List[Dict]:
        pass

        """
        벡터 검색 (쿼리 벡터 기준)
        Optional 필터 지원 (Qdrant만 제대로 활용 가능, FAISS는 무시 가능)
        """
        pass
