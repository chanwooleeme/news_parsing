from agentic_retriever.evaluator.sufficiency_checker import SufficiencyChecker
from agentic_retriever.config.models import ModelName
from typing import List
from utils.config import BASE_API_URL
import requests
from logger import get_logger

logger = get_logger(__name__)

def update_importance(point_id, importance):
    url = BASE_API_URL + "/update-article-importance"
    requests.post(url, json={"point_id": point_id, "importance": importance})
    logger.info("update_importance point_id: " + point_id)

def check_sufficient_task(articles, openai_client) -> List[dict]:
    checker = SufficiencyChecker(openai_client, model=ModelName.GPT_4O_MINI)
    sufficiency_result = checker.check_sufficiency(articles)
    
    sufficient_summaries = []
    for result in sufficiency_result:
        importance = int(result['importance'])
        if importance >= 3:
            sufficient_summaries.append({
                "id" : result['id'],
                "importance" : importance,
                "content": result['content']
            })
        update_importance(result['id'], importance)

    return sufficient_summaries
