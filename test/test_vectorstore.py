from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from clients.qdrant_vector_store import QdrantVectorStore
from vector_store.vector_store import NewsVectorStore
import random
import time

QDRANT_URL='https://78cfd54a-d28f-47d1-bbee-f0cdd20bd631.us-east-1-0.aws.cloud.qdrant.io'
QDRANT_API_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.wENRbz8H9K4bluQ-3RsewxfRHc-tWRN1TFw857p7gWg'

# 1. QdrantClient 세팅 (환경 맞게 URL 수정)
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

collection_name = "test-batch-speed"

def ensure_collection_exists(qdrant_client: QdrantClient, collection_name: str):
    if not qdrant_client.collection_exists(collection_name=collection_name):
        print(f"컬렉션 '{collection_name}' 없음 → 새로 생성합니다.")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE
            )
        )
    else:
        print(f"컬렉션 '{collection_name}' 이미 존재함.")

ensure_collection_exists(qdrant_client, collection_name)

vector_store = QdrantVectorStore(
    qdrant_client=qdrant_client,
    collection_name=collection_name,
    max_workers=10
)

# 더미 데이터 생성
def generate_dummy_data(count: int):
    vectors_and_metadata = []
    economic_vars = ["금", "주식", "환율", "에너지", "부동산"]

    for i in range(count):
        vector = [random.uniform(-1, 1) for _ in range(1536)]
        metadata = {
            "title": f"속도비교 기사 {i+1}",
            "content": f"속도 비교용 더미 기사 {i+1}번 본문.",
            "economic_variables": [random.choice(economic_vars)],
            "publication_date": 1712900000 + i * 10000
        }
        vectors_and_metadata.append((vector, metadata))
    return vectors_and_metadata

# 순차 저장
def sequential_insert(store: QdrantVectorStore, vectors_and_metadata):
    ids = []
    for vector, metadata in vectors_and_metadata:
        point_id = store.insert(vector, metadata)
        ids.append(point_id)
    return ids

if __name__ == "__main__":
    dummy_data = generate_dummy_data(1000)

    # 순차 저장 측정
    print("\n[순차 저장 테스트]")
    start = time.time()
    sequential_insert(vector_store, dummy_data)
    end = time.time()
    print(f"순차 저장 소요 시간: {end - start:.2f}초")

    # 컬렉션 비우고 다시!
    qdrant_client.delete_collection(collection_name)
    ensure_collection_exists(qdrant_client, collection_name)

    # 병렬 저장 측정
    print("\n[병렬 저장 테스트]")
    start = time.time()
    vector_store.batch_insert(dummy_data)
    end = time.time()
    print(f"병렬 저장 소요 시간: {end - start:.2f}초")