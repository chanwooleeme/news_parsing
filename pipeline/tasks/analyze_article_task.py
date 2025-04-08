from typing import List, Dict
from nli.classifier import NLIClassifier
from common.logger import get_logger

logger = get_logger(__name__)

def analyze_article_task(
    embedded_articles: List[Dict],
    top_k: int = 3
) -> List[Dict]:
    """
    새 기사와 검색된 기사들 간의 관계(NLI)를 분석하는 태스크.

    Args:
        embedded_articles: embed_and_search_task 결과 리스트
        top_k: 검색 결과 중 상위 몇 개를 비교할지

    Returns:
        관계 분석된 결과 리스트
    """

    classifier = NLIClassifier()

    final_results = []

    for article_info in embedded_articles:
        new_article = article_info["new_article"]
        search_results = article_info["search_results"]

        relationships = []

        for search_result in search_results[:top_k]:
            try:
                relationship = classifier.classify_relationship(
                    new_article=new_article["content"],
                    existing_article=search_result["content"]
                )

                relationships.append({
                    "existing_article_title": search_result["title"],
                    "relationship": relationship,
                    "score": search_result["score"],
                })

            except Exception as e:
                logger.error(f"NLI 분석 실패: {e}")

        final_results.append({
            "new_article": new_article,
            "relationships": relationships
        })

    return final_results
