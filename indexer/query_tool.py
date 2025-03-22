import os
import logging
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import qdrant_client
import openai

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 환경변수 설정
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY")
QDRANT_ENDPOINT    = os.environ.get("QDRANT_ENDPOINT", "https://78cfd54a-d28f-47d1-bbee-f0cdd20bd631.us-east-1-0.aws.cloud.qdrant.io")
QDRANT_API_KEY     = os.environ.get("QDRANT_API_KEY")
QDRANT_COLLECTION  = "openi"

if not all([OPENAI_API_KEY, QDRANT_API_KEY]):
    raise ValueError("필요한 API 키가 환경 변수에 설정되지 않았습니다.")

def initialize_index():
    """Qdrant 클라이언트와 인덱스를 초기화합니다."""
    try:
        # Qdrant 클라이언트 설정
        client = qdrant_client.QdrantClient(
            url=QDRANT_ENDPOINT,
            api_key=QDRANT_API_KEY
        )
        
        # 벡터 스토어 설정
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION
        )
        
        # OpenAI 임베딩 모델 설정
        embed_model = OpenAIEmbedding(
            api_key=OPENAI_API_KEY,
            model="text-embedding-ada-002"
        )
        
        # 스토리지 컨텍스트 생성
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # 인덱스 로드
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            embed_model=embed_model
        )
        
        return index
    
    except Exception as e:
        logger.error(f"Error initializing index: {e}")
        raise

def search_articles(index, query, top_k=5):
    """
    주어진 쿼리로 기사를 검색합니다.
    
    Args:
        index: VectorStoreIndex 인스턴스
        query: 검색 쿼리 문자열
        top_k: 반환할 결과 수
    """
    try:
        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        
        print(f"\n검색 결과 ({len(nodes)} 건):\n")
        for i, node in enumerate(nodes, 1):
            # 노드의 메타데이터에서 정보 추출
            metadata = node.node.metadata
            extra_info = node.node.extra_info
            
            print(f"=== 결과 {i} ===")
            print(f"제목: {extra_info.get('title', 'N/A')}")
            print(f"작성자: {extra_info.get('author', 'N/A')}")
            print(f"카테고리: {extra_info.get('category', 'N/A')}")
            print(f"발행일: {extra_info.get('published_time', 'N/A')}")
            print(f"URL: {extra_info.get('url', 'N/A')}")
            print(f"관련도 점수: {node.score:.4f}")
            print(f"내용 미리보기: {node.node.text[:200]}...\n")
            
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise

def main():
    try:
        print("뉴스 기사 검색 시스템을 초기화하는 중...")
        index = initialize_index()
        print("초기화 완료!")
        
        while True:
            query = input("\n검색어를 입력하세요 (종료하려면 'q' 입력): ")
            
            if query.lower() == 'q':
                print("프로그램을 종료합니다.")
                break
            
            if not query.strip():
                print("검색어를 입력해주세요.")
                continue
            
            search_articles(index, query)
            
    except Exception as e:
        logger.error(f"Error in main program: {e}")
        return

if __name__ == "__main__":
    main() 