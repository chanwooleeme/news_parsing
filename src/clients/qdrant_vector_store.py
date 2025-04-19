from src.clients.vector_store import VectorStore
from typing import List, Dict, Tuple, Optional, Any
import uuid
import concurrent.futures
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.models import Filter as QdrantFilter

class QdrantVectorStore(VectorStore):
    def __init__(self, qdrant_client: QdrantClient, collection_name: str = "economy-articles", max_workers: int = 10):
        self.qdrant = qdrant_client
        self.collection_name = collection_name
        self.max_workers = max_workers

    def insert(self, vector: List[float], metadata: Optional[Dict[str, str]] = None) -> str:
        """
        단일 벡터 저장
        """
        point_id = str(uuid.uuid4())
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=metadata or {}
                )
            ]
        )
        return point_id

    def batch_insert(self, vectors_and_metadata: List[Tuple[List[float], Dict[str, str]]]) -> List[str]:
        """
        여러 벡터 병렬 저장
        """
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_data = {
                executor.submit(self.insert, vector, metadata): (i, vector, metadata)
                for i, (vector, metadata) in enumerate(vectors_and_metadata)
            }

            for future in tqdm(concurrent.futures.as_completed(future_to_data), total=len(vectors_and_metadata), desc="벡터 저장"):
                i, vector, metadata = future_to_data[future]
                try:
                    point_id = future.result()
                    results.append(point_id)
                except Exception as e:
                    print(f"벡터 저장 실패 (인덱스 {i}): {e}")
                    results.append(None)

        return results

    def search(self, query_vector: Optional[List[float]], top_k: int = 5, query_filter: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        벡터 검색 또는 필터 검색
        """
        qdrant_filter = None
        if query_filter:
            if isinstance(query_filter, QdrantFilter):
                qdrant_filter = query_filter
            elif isinstance(query_filter, dict):
                qdrant_filter = QdrantFilter(**query_filter)
            else:
                raise ValueError("query_filter must be a dict or Qdrant Filter object")

        if query_vector is None:
            # 벡터 없이 필터만으로 검색
            scroll_result = self.qdrant.scroll(
                collection_name=self.collection_name,
                scroll_filter=qdrant_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )
            points = scroll_result[0]
        else:
            # 벡터 기반 검색
            search_result = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )
            points = search_result

        articles = []
        for point in points:
            payload = point.payload or {}
            articles.append({
                "id": point.id,
                "score": getattr(point, "score", None),  # scroll 결과는 score 없을 수 있음
                "payload": payload
            })

        return articles
