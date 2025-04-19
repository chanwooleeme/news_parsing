from typing import List, Dict
from logging import getLogger
from utils.file import list_directories, list_files, join_path, read_json_file
import asyncio
import aiohttp

logger = getLogger(__name__)
MAX_BATCH_SIZE = 1000

# 📰 기사 로딩
def load_articles_from_directory(base_dir: str) -> List[Dict]:
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
                elif len(content) <= 100:
                    logger.warning(f"❌ Content 길이 너무 짧은 기사: {json_path}")
                    continue

                articles.append(article)
            except Exception as e:
                logger.error(f"❌ {newspaper}/{filename} 읽기 실패: {e}")
    
    logger.info(f"총 {len(articles)}개 기사 수집 완료")
    return articles

# 🧩 배치 나누기
def batch_articles(articles: List[Dict], batch_size: int = MAX_BATCH_SIZE) -> List[List[Dict]]:
    return [articles[i:i + batch_size] for i in range(0, len(articles), batch_size)]

# 🚀 비동기 API 호출
async def async_call_predict(session, batch, idx):
    try:
        async with session.post("http://34.64.121.216:8000/api/v1/predict", json=batch) as resp:
            logger.info(f"✅ Batch {idx} 응답 코드: {resp.status}")
    except Exception as e:
        logger.error(f"❌ Batch {idx} 실패: {e}")

async def async_predict_all_batches(batches):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        tasks = [async_call_predict(session, batch, idx+1) for idx, batch in enumerate(batches)]
        await asyncio.gather(*tasks)

# 🎯 최종 실행 함수
def predict_economy_articles_task(parsed_dir: str):
    articles = load_articles_from_directory(parsed_dir)
    batches = batch_articles(articles)

    logger.info(f"🚀 총 {len(batches)}개 배치 async 요청 시작")
    asyncio.run(async_predict_all_batches(batches))
    logger.info("✅ 모든 기사 예측 요청 완료 (서버에서 자동 처리)")
