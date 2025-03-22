import os
import logging
import boto3
import pandas as pd
import qdrant_client
import time
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from rouge import Rouge
from openai import OpenAI

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 환경변수 세팅
SOURCE_BUCKET      = "article-crawl-parquet-storage"
LOCAL_DOWNLOAD_DIR = "./test_parquet_files"
SAMPLE_FILE        = "sampled_data.parquet"
INDEX_FILE         = "test_index.json"

# API 키 설정
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY")
QDRANT_API_KEY     = os.environ.get("QDRANT_API_KEY")
GOOGLE_API_KEY     = os.environ.get("GOOGLE_API_KEY")

if not all([OPENAI_API_KEY, QDRANT_API_KEY, GOOGLE_API_KEY]):
    raise ValueError("필요한 API 키가 환경 변수에 설정되지 않았습니다.")

QDRANT_ENDPOINT    = "https://78cfd54a-d28f-47d1-bbee-f0cdd20bd631.us-east-1-0.aws.cloud.qdrant.io"
QDRANT_COLLECTION  = "openi"

# 디렉토리 생성
if not os.path.exists(LOCAL_DOWNLOAD_DIR):
    os.makedirs(LOCAL_DOWNLOAD_DIR)

def load_and_sample_parquet_files():
    """LOCAL_DOWNLOAD_DIR에 있는 모든 Parquet 파일을 읽어와서 무작위로 100개 샘플링"""
    all_data = pd.DataFrame()
    
    for filename in os.listdir(LOCAL_DOWNLOAD_DIR):
        if filename.endswith(".parquet"):
            file_path = os.path.join(LOCAL_DOWNLOAD_DIR, filename)
            logger.info(f"Loading {file_path}")
            df = pd.read_parquet(file_path)
            all_data = pd.concat([all_data, df], ignore_index=True)
    
    logger.info(f"Total records loaded: {len(all_data)}")
    
    # 무작위로 100개 샘플링
    sampled_df = all_data.sample(n=100, random_state=42)
    sampled_df.to_parquet(SAMPLE_FILE)
    logger.info(f"샘플링된 데이터가 {SAMPLE_FILE}에 저장되었습니다.")
    
    return sampled_df

def create_documents(df):
    """데이터프레임에서 문서 객체 생성"""
    df = df[df['content_text'].notnull()]
    documents = []
    
    for _, row in df.iterrows():
        title = row.get('title', 'No Title') if pd.notnull(row.get('title')) else 'No Title'
        full_text = f"{title}\n{row['content_text']}"
        
        doc = Document(
            text=full_text,
            extra_info={
                "title": title,
                "article_id": row.get("article_id"),
                "author": row.get("author"),
                "category": row.get("category"),
                "url": row.get("url"),
                "published_time": row.get("published_time"),
                "year": int(row.get("year")) if pd.notnull(row.get("year")) else None,
                "month": row.get("month"),
                "day": row.get("day"),
            }
        )
        documents.append(doc)
    
    return documents

def setup_qdrant():
    """Qdrant 컬렉션 설정"""
    client = qdrant_client.QdrantClient(url=QDRANT_ENDPOINT, api_key=QDRANT_API_KEY)

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config={"size": 1536, "distance": "Cosine"}
    )
    
    return client

def main():
    logger.info("=== 테스트 인덱싱 시작 ===")
    
    # 1. Qdrant 설정
    qdrant_client = setup_qdrant()
    logger.info("Qdrant 컬렉션 설정 완료")
    
    sampled_df = pd.read_parquet(SAMPLE_FILE)

    # 4. 문서 생성
    documents = create_documents(sampled_df)
    logger.info(f"문서 {len(documents)}개 생성 완료")
    
    # 5. 인덱싱
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=QDRANT_COLLECTION)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = OpenAIEmbedding(api_key=OPENAI_API_KEY, model="text-embedding-ada-002")
    
    logger.info("인덱싱 시작...")
    start_time = time.time()
    
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True
    )
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"인덱싱 완료. 소요 시간: {elapsed_time:.2f}초")
    
    # 인덱스 저장
    index.storage_context.persist(persist_dir=INDEX_FILE)
    logger.info(f"인덱스가 {INDEX_FILE}에 저장되었습니다.")
    
    logger.info("=== 테스트 인덱싱 완료 ===")

if __name__ == "__main__":
    main()