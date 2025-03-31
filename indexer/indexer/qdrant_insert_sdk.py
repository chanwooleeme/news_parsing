import os
import json
import logging
from typing import Dict, List
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def load_results(jsonl_path: str) -> Dict[str, List[float]]:
    """OpenAI 결과 파일에서 custom_id → embedding 벡터 추출"""
    results = {}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            if "response" in obj and obj["response"].get("status_code") == 200:
                embedding = obj["response"]["body"]["data"][0]["embedding"]
                custom_id = obj["custom_id"]
                results[custom_id] = embedding
            else:
                logging.warning(f"❌ 실패 또는 오류 응답: {obj.get('custom_id')}")
    return results


def load_metadata(metadata_path: str) -> Dict[str, Dict]:
    """메타데이터 파일에서 custom_id → payload 매핑"""
    with open(metadata_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {item["custom_id"]: item for item in raw}


def insert_embeddings_to_qdrant(qdrant_client: QdrantClient, jsonl_dir: str, collection_name: str) -> None:
    """결과 벡터 + 메타데이터를 Qdrant에 업서트"""
    for filename in os.listdir(jsonl_dir):
        if not filename.endswith("_results.jsonl"):
            continue

        base_name = filename.replace("_results.jsonl", "")
        metadata_name = base_name.replace("embedding", "metadata") + ".json"
        result_path = os.path.join(jsonl_dir, filename)
        metadata_path = os.path.join(jsonl_dir, metadata_name)

        if not os.path.exists(metadata_path):
            logging.warning(f"⚠️ 메타데이터 파일 없음: {metadata_name}")
            continue

        logging.info(f"📥 처리 중: {filename}")
        results = load_results(result_path)
        metadata = load_metadata(metadata_path)

        points = []
        for custom_id, vector in results.items():
            meta = metadata.get(custom_id)
            if not meta:
                logging.warning(f"❓ 메타데이터 없음: {custom_id}")
                continue
            payload = meta.copy()
            payload.pop("content", None)
            payload.pop("index", None)

            point = PointStruct(id=custom_id, vector=vector, payload=payload)
            points.append(point)

        if not points:
            logging.warning("⛔ 업서트할 포인트가 없습니다.")
            continue

        qdrant_client.upsert(collection_name=collection_name, points=points)
        logging.info(f"✅ {len(points)}개 포인트 업서트 완료: {collection_name}")

