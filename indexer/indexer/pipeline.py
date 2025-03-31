import os
import logging
from openai import OpenAI
from qdrant_client import QdrantClient

# 유틸 함수들 - 절대 경로로 임포트
from indexer.utils import (
    get_html_files,
    load_parser_factory,
    parse_articles_by_newspaper,
    save_batch_files,
)
from indexer.openai_batch_upload_sdk import run_batch_sdk
from indexer.qdrant_insert_sdk import insert_embeddings_to_qdrant

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run_pipeline():
    # === 환경 변수 가져오기 ===
    html_dir = os.environ.get("RSS_FEED_HTML_DIR", "/opt/airflow/data/html")
    output_dir = os.environ.get("PARSER_JSONL_DIR", "/opt/airflow/data/jsonl")

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    qdrant_host = os.environ.get("QDRANT_HOST")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    qdrant_collection = os.environ.get("QDRANT_COLLECTION", "news-articles")

    if not all([openai_api_key, qdrant_host, qdrant_api_key]):
        logging.error("필수 환경 변수가 누락되었습니다. OPENAI_API_KEY, QDRANT_HOST, QDRANT_API_KEY를 확인하세요.")
        return

    # === 파서 준비 및 HTML 로드 ===
    factory = load_parser_factory()
    html_files = get_html_files(html_dir)
    if not html_files:
        logging.warning("HTML 파일이 없습니다.")
        return

    logging.info(f"{len(html_files)}개의 HTML 파일 발견됨")
    newspaper_groups = parse_articles_by_newspaper(factory, html_files, html_dir)
    batch_files = save_batch_files(newspaper_groups, output_dir)

    if not batch_files:
        logging.warning("배치 파일이 생성되지 않았습니다.")
        return

    # === OpenAI 클라이언트 준비 ===
    client = OpenAI(api_key=openai_api_key)

    # === 배치 업로드 및 결과 다운로드 ===
    run_batch_sdk(client=client, jsonl_dir=output_dir)

    # === Qdrant 클라이언트 준비 ===
    qdrant = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)

    # === 결과를 Qdrant에 업서트 ===
    insert_embeddings_to_qdrant(qdrant_client=qdrant, jsonl_dir=output_dir, collection_name=qdrant_collection)

    logging.info("✅ 전체 파이프라인 완료!")


if __name__ == "__main__":
    run_pipeline()
