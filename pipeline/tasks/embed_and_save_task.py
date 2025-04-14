from typing import List, Dict, Tuple
from utils.file import (
    read_json_file,
    list_directories,
    list_files,
    join_path,
)
from embedding.embedding import NewsEmbedding
from vector_store.vector_store import NewsVectorStore
from clients.qdrant_vector_store import QdrantVectorStore
from logger import get_logger
from utils.client import get_openai_client, get_qdrant_client

logger = get_logger(__name__)

def load_articles_from_directory(base_dir: str) -> List[Dict]:
    """디렉토리에서 json 파일 읽어와서 기사 리스트로 반환"""
    articles = []

    for newspaper in list_directories(base_dir):
        newspaper_dir = join_path(base_dir, newspaper)
        for filename in list_files(newspaper_dir, extension=".json"):
            json_path = join_path(newspaper_dir, filename)
            try:
                article = read_json_file(json_path)
                content = article.get("content", "")

                if not content:
                    logger.warning(f"❌ Content 비어있음: {json_path}")
                    continue
                elif len(content) <= 300:
                    logger.warning(f"❌ Content 길이 너무 짧은 기사: {json_path}")
                    continue

                articles.append(article)
            except Exception as e:
                logger.error(f"❌ {newspaper}/{filename} 읽기 실패: {e}")
    
    logger.info(f"총 {len(articles)}개 기사 수집 완료")
    return articles

def embed_and_save_task(parsed_base_dir: str) -> int:
    """기사 임베딩 생성 후 Qdrant에 저장하는 메인 태스크"""
    logger.info(f"===== 임베딩 생성 및 저장 태스크 시작 =====")
    
    # 1. 기사 수집
    articles = load_articles_from_directory(parsed_base_dir)
    contents = [article.get("content", "") for article in articles]
    
    # 2. 임베딩 생성
    embedder = NewsEmbedding(get_openai_client())
    embeddings = embedder.embed_batch(contents)
    
    logger.info(f"총 {len(embeddings)}개 임베딩 생성 완료")
    
    # 3. 기사-임베딩 매칭
    vectors_and_metadata = []
    for article, embedding in zip(articles, embeddings):
        if embedding:  # 임베딩이 성공적으로 생성된 경우만
            vectors_and_metadata.append((embedding, article))
    
    logger.info(f"총 {len(vectors_and_metadata)}개 기사-임베딩 매칭 완료")
    
    # 4. Qdrant에 저장
    vector_store = NewsVectorStore(QdrantVectorStore(get_qdrant_client(), collection_name="economy-articles"))
    point_ids = vector_store.batch_insert(vectors_and_metadata)
    
    success_count = len([pid for pid in point_ids if pid])
    fail_count = len([pid for pid in point_ids if pid is None])

    logger.info(f"✅ 벡터 저장 성공: {success_count}, 실패: {fail_count}")
    logger.info(f"===== 임베딩 생성 및 저장 태스크 완료 =====")
    
    return success_count

if __name__ == "__main__":
    import os
    count = embed_and_save_task(
        parsed_base_dir=os.getenv('PARSED_ARTICLES_DIR', '/Users/lee/Desktop/news_parsing/data/parsed_articles')
    )
    print(f"총 {count}개 기사 임베딩 생성 및 저장 완료")
