import os
import time
import logging
from openai import OpenAI

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def upload_batch_file(client: OpenAI, file_path: str):
    with open(file_path, "rb") as f:
        return client.files.create(file=f, purpose="batch")


def create_batch(client: OpenAI, file_id: str, metadata: dict = None):
    return client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/embeddings",
        completion_window="24h",
        metadata=metadata or {}
    )


def poll_until_done(client: OpenAI, batch_id: str, interval: int = 10) -> str:
    while True:
        batch = client.batches.retrieve(batch_id)
        logging.info(f"⏳ 현재 상태: {batch.status}")
        if batch.status == "completed":
            return batch.output_file_id
        elif batch.status in {"failed", "cancelled", "expired"}:
            raise RuntimeError(f"Batch {batch_id} 실패 또는 취소됨: {batch.status}")
        time.sleep(interval)


def download_batch_result(client: OpenAI, file_id: str, save_path: str):
    content = client.files.content(file_id)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content.text)
    logging.info(f"✅ 결과 저장됨: {save_path}")


def run_batch_sdk(client: OpenAI, jsonl_dir: str) -> None:
    """주어진 디렉토리 내 모든 .jsonl 배치 파일을 OpenAI Batch API로 업로드하고 결과 저장"""
    for filename in os.listdir(jsonl_dir):
        if not filename.endswith(".jsonl") or "_embedding_" not in filename:
            continue

        filepath = os.path.join(jsonl_dir, filename)
        logging.info(f"📤 업로드 중: {filename}")

        try:
            uploaded = upload_batch_file(client, filepath)
            logging.info(f"✅ 업로드 완료: {uploaded.id}")

            batch = create_batch(client, uploaded.id, metadata={"source": filename})
            logging.info(f"🚀 배치 생성됨: {batch.id}")

            output_file_id = poll_until_done(client, batch.id)
            result_path = filepath.replace(".jsonl", "_results.jsonl")
            download_batch_result(client, output_file_id, result_path)

        except Exception as e:
            logging.error(f"❌ {filename} 처리 실패: {e}")

