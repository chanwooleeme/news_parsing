import os
from typing import List, Dict
from utils.file import save_dict_as_json, make_directory
from common.logger import get_logger

logger = get_logger(__name__)

def save_analysis_task(
    analyzed_results: List[Dict],
    save_base_dir: str
) -> None:
    """
    분석된 기사 결과를 저장하는 태스크.

    Args:
        analyzed_results: analyze_article_task 결과 리스트
        save_base_dir: 결과 JSON 파일 저장할 최상위 디렉토리 경로
    """

    for result in analyzed_results:
        try:
            article = result["new_article"]
            relationships = result["relationships"]

            newspaper = article.get("category", "unknown")  # 없으면 unknown
            article_id = article.get("custom_id", "")

            if not article_id:
                logger.warning(f"❌ custom_id 없음, 저장 스킵")
                continue

            save_dir = os.path.join(save_base_dir, newspaper)
            make_directory(save_dir)

            save_dict_as_json(
                data={
                    "article": article,
                    "relationships": relationships
                },
                save_dir=save_dir,
                filename=article_id
            )

            logger.info(f"✅ 분석 결과 저장 완료: {save_dir}/{article_id}.json")

        except Exception as e:
            logger.error(f"❌ 저장 실패: {e}")
