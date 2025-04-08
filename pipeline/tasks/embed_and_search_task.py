from utils.file import (
    read_json_file,
    list_directories,
    list_files,
    join_path,
)
from indexer.embedder import NewsEmbedder
from retriever.retriever import NewsRetriever
from common.logger import get_logger
from typing import List, Dict

logger = get_logger(__name__)

def embed_and_search_task(parsed_base_dir: str, top_k: int = 5) -> List[Dict]:
    embedder = NewsEmbedder()
    retriever = NewsRetriever(embedder=embedder)
    results = []

    for newspaper in list_directories(parsed_base_dir):
        newspaper_dir = join_path(parsed_base_dir, newspaper)

        for filename in list_files(newspaper_dir, extension=".json"):
            json_path = join_path(newspaper_dir, filename)
            try:
                article = read_json_file(json_path)
                content = article.get("content", "")

                if not content:
                    logger.warning(f"❌ Content 비어있음: {json_path}")
                    continue

                embedding = embedder.embed_text(content)

                search_results = retriever.search(
                    query=content,
                    top_k=top_k
                )

                results.append({
                    "new_article": article,
                    "embedding": embedding,
                    "search_results": search_results
                })

                logger.info(f"✅ {newspaper}/{filename} 임베딩 & 검색 완료")
            except Exception as e:
                logger.error(f"❌ {newspaper}/{filename} 처리 실패: {e}")

    return results


if __name__ == "__main__":
    import os
    embed_and_search_task(
        parsed_base_dir=os.getenv('PARSED_ARTICLES_DIR', 'parsed_articles'),
        top_k=os.getenv('TOP_K', 5)
    )
