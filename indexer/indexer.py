import os
import logging
import boto3
import pandas as pd
import openai
import qdrant_client
import time
import json
from multiprocessing import Pool, cpu_count

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 환경변수 세팅
SOURCE_BUCKET      = os.environ.get("SOURCE_BUCKET", "article-crawl-parquet-storage")
OUTPUT_BUCKET      = os.environ.get("OUTPUT_BUCKET", "article-crawl-index-storage")  # 인덱스 파일 저장할 S3 버킷
LOCAL_DOWNLOAD_DIR = os.environ.get("LOCAL_DOWNLOAD_DIR", "./parquet_files")
INDEX_FILE         = "merged_index.json"  # 저장할 인덱스 파일명
CHECKPOINT_FILE    = "checkpoint.json"    # 진행 상황 저장 파일

# API 키 설정
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY")
QDRANT_API_KEY     = os.environ.get("QDRANT_API_KEY")

if not all([OPENAI_API_KEY, QDRANT_API_KEY]):
    raise ValueError("필요한 API 키가 환경 변수에 설정되지 않았습니다.")

openai.api_key     = OPENAI_API_KEY

# Qdrant Cloud 환경변수
QDRANT_ENDPOINT    = os.environ.get("QDRANT_ENDPOINT", "https://78cfd54a-d28f-47d1-bbee-f0cdd20bd631.us-east-1-0.aws.cloud.qdrant.io")
QDRANT_COLLECTION  = os.environ.get("QDRANT_COLLECTION", "articles")

if not os.path.exists(LOCAL_DOWNLOAD_DIR):
    os.makedirs(LOCAL_DOWNLOAD_DIR)
    logger.info(f"Created local download directory: {LOCAL_DOWNLOAD_DIR}")

def save_checkpoint(processed_chunks):
    checkpoint = {"processed_chunks": processed_chunks}
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f)
    logger.info(f"Checkpoint saved: {checkpoint}")

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        logger.info(f"Checkpoint loaded: {checkpoint}")
        return checkpoint.get("processed_chunks", 0)
    return 0

def list_all_parquet_keys(s3_client, bucket):
    logger.info(f"Listing all .parquet files in bucket '{bucket}'...")
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket)
    parquet_keys = []
    for page in page_iterator:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith(".parquet"):
                parquet_keys.append(key)
    logger.info(f"Found {len(parquet_keys)} parquet files.")
    return parquet_keys

def load_parquet_file(local_file):
    try:
        df = pd.read_parquet(local_file)
        logger.info(f"Loaded {local_file} with {len(df)} records.")
        return df
    except Exception as e:
        logger.exception(f"Error loading {local_file}: {e}")
        return pd.DataFrame()

def create_documents_from_df(df):
    df = df[df['content_text'].notnull()]
    documents = []
    for _, row in df.iterrows():
        title = row.get('title', 'No Title') if pd.notnull(row.get('title')) else 'No Title'
        full_text = f"{title}\n{row['content_text']}"
        doc = Document(
            text=full_text,
            extra_info={
                "title": title,  # 제목을 extra_info에도 추가
                "article_id": row.get("article_id"),
                "author": row.get("author"),
                "category": row.get("category"),
                "url": row.get("url"),
                "published_time": row.get("published_time"),
                "year": int(row.get("year")) if pd.notnull(row.get("year")) else None,  # year를 정수로 저장
                "month": row.get("month"),
                "day": row.get("day"),
            }
        )
        documents.append(doc)
    logger.info(f"Created {len(documents)} Document objects from DataFrame.")
    return documents

def download_and_extract_documents(s3_client, key):
    local_path = os.path.join(LOCAL_DOWNLOAD_DIR, os.path.basename(key))
    try:
        logger.info(f"Downloading {key} to {local_path}...")
        s3_client.download_file(SOURCE_BUCKET, key, local_path)
        logger.info(f"Downloaded {key} successfully.")
    except Exception as e:
        logger.exception(f"Failed to download {key}: {e}")
        return []
    
    df = load_parquet_file(local_path)
    if df.empty or df['content_text'].isnull().all():
        logger.warning(f"No valid records in {local_path}. Skipping file.")
        os.remove(local_path)
        return []
    
    documents = create_documents_from_df(df)
    os.remove(local_path)
    logger.info(f"Removed local file {local_path}.")
    return documents

def create_index_chunk(doc_chunk, chunk_index, total_chunks, max_retries=3, retry_delay=2):
    """
    각 워커 프로세스에서 doc_chunk에 대한 인덱스를 생성합니다.
    chunk_index와 total_chunks를 추가하여 전체 진행상황을 표시합니다.
    """
    try:
        client = qdrant_client.QdrantClient(url=QDRANT_ENDPOINT, api_key=QDRANT_API_KEY)
        vector_store = QdrantVectorStore(client=client, collection_name=QDRANT_COLLECTION)
        storage_context_local = StorageContext.from_defaults(vector_store=vector_store)
        local_embed_model = OpenAIEmbedding(api_key=OPENAI_API_KEY, model="text-embedding-ada-002")
        
        # 더 작은 배치 사이즈로 나누어 처리
        batch_size = 50
        total_batches = len(doc_chunk) // batch_size + (1 if len(doc_chunk) % batch_size else 0)
        
        for batch_idx in range(0, len(doc_chunk), batch_size):
            current_batch = batch_idx // batch_size + 1
            batch = doc_chunk[batch_idx:batch_idx + batch_size]
            
            logger.info(f"Chunk {chunk_index}/{total_chunks} - Batch {current_batch}/{total_batches} "
                       f"(Processing {len(batch)} documents)")
            
            index_batch = VectorStoreIndex.from_documents(
                batch,
                storage_context=storage_context_local,
                embed_model=local_embed_model,
                show_progress=True
            )
            
            # 진행률 계산
            total_progress = ((chunk_index - 1) * 100 + (current_batch / total_batches) * 100) / total_chunks
            logger.info(f"Overall Progress: {total_progress:.2f}%")
            
            time.sleep(3)  # TPM 제한 고려한 대기
        
        return index_batch
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Error in chunk {chunk_index}/{total_chunks}: {e}")
        if "insufficient_quota" in error_msg:
            return "quota_exceeded"
        return None

def merge_index_chunks(index_chunks):
    """
    각 인덱스 조각(index_chunks)의 docstore에서 노드를 추출하고,
    해당 노드에 embedding 정보를 복원하여 하나의 인덱스로 merge 합니다.
    """
    all_nodes = []
    for idx in index_chunks:
        if idx is None or idx == "quota_exceeded":
            continue
        vector_store_dict = idx.storage_context.vector_store.to_dict()
        embedding_dict = vector_store_dict.get('embedding_dict', {})
        for doc_id, node in idx.storage_context.docstore.docs.items():
            if doc_id in embedding_dict:
                node.embedding = embedding_dict[doc_id]
            all_nodes.append(node)
    logger.info(f"Merged a total of {len(all_nodes)} nodes from index chunks.")
    merged_index = VectorStoreIndex(nodes=all_nodes)
    return merged_index

def main():
    logger.info("Starting indexing process.")
    
    s3_client = boto3.client("s3")
    parquet_keys = list_all_parquet_keys(s3_client, SOURCE_BUCKET)
    
    # 전체 문서 수 계산 및 표시
    all_documents = []
    total_files = len(parquet_keys)
    for file_index, key in enumerate(parquet_keys, start=1):
        docs = download_and_extract_documents(s3_client, key)
        if docs:
            all_documents.extend(docs)
            logger.info(f"[{file_index}/{total_files}] Loaded {len(docs)} documents from {key}. "
                       f"Total documents so far: {len(all_documents)}")
    
    if not all_documents:
        logger.error("No documents to index. Exiting process.")
        return

    chunk_size = 100
    doc_chunks = [all_documents[i:i + chunk_size] for i in range(0, len(all_documents), chunk_size)]
    total_chunks = len(doc_chunks)
    logger.info(f"Total {len(all_documents)} documents divided into {total_chunks} chunks "
                f"(chunk size: {chunk_size})")
    
    processed_chunks = load_checkpoint()
    logger.info(f"Resuming from chunk {processed_chunks + 1}/{total_chunks} "
                f"({(processed_chunks/total_chunks*100):.2f}% completed)")

    num_workers = min(2, cpu_count())
    logger.info(f"Starting parallel processing with {num_workers} workers...")
    
    index_chunks = []
    with Pool(processes=num_workers) as pool:
        for idx, chunk in enumerate(doc_chunks[processed_chunks:], start=processed_chunks + 1):
            logger.info(f"\n{'='*50}\nProcessing chunk {idx}/{total_chunks} "
                       f"({(idx/total_chunks*100):.2f}% of total)")
            result = pool.apply(create_index_chunk, args=(chunk, idx, total_chunks))
            
            if result == "quota_exceeded":
                logger.error("Quota exceeded during chunk processing. Halting further processing.")
                save_checkpoint(idx)
                break
                
            index_chunks.append(result)
            save_checkpoint(idx)
            
            remaining_chunks = total_chunks - idx
            logger.info(f"Completed chunk {idx}/{total_chunks}. "
                       f"Remaining chunks: {remaining_chunks} "
                       f"({(remaining_chunks/total_chunks*100):.2f}% remaining)")

    # 필터링: None이나 "quota_exceeded" 결과는 제거
    index_chunks = [idx for idx in index_chunks if idx not in (None, "quota_exceeded")]
    if not index_chunks:
        logger.error("No index chunks were successfully created. Exiting process.")
        return

    try:
        logger.info("Merging index chunks via node extraction...")
        merged_index = merge_index_chunks(index_chunks)
        logger.info("Merged index successfully created via node extraction.")
    except Exception as e:
        logger.exception(f"Error merging index chunks: {e}")
        return

    try:
        merged_index.save_to_disk(INDEX_FILE)
        logger.info(f"Index saved locally as {INDEX_FILE}.")
    except Exception as e:
        logger.exception(f"Failed to save index to disk: {e}")
        return

    try:
        logger.info(f"Uploading {INDEX_FILE} to S3 bucket '{OUTPUT_BUCKET}'...")
        s3_client.upload_file(INDEX_FILE, OUTPUT_BUCKET, INDEX_FILE)
        logger.info(f"Uploaded {INDEX_FILE} to S3 bucket '{OUTPUT_BUCKET}' successfully.")
    except Exception as e:
        logger.exception(f"Failed to upload index to S3: {e}")
        return

    try:
        os.remove(INDEX_FILE)
        logger.info(f"Removed local index file {INDEX_FILE}.")
    except Exception as e:
        logger.exception(f"Failed to remove local index file {INDEX_FILE}: {e}")

    logger.info("Indexing process completed successfully.")

if __name__ == "__main__":
    main()
