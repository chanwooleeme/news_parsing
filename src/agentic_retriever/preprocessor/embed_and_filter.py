import os
import sys
from typing import List, Dict, Any, Tuple
import json
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI
from clients.qdrant_vector_store import QdrantVectorStore
from utils.client import get_qdrant_client, get_openai_client
from utils.file import list_directories, list_files, join_path, read_json_file

# 로거 설정 (logger.py 모듈 사용 시 대체 가능)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# ─────────────────────────────
# 상수: 경제/비경제 관련 키워드 테이블 및 GOOD_QUERIES
# ─────────────────────────────
ECONOMY_KEYWORD_WEIGHTS = {
    "경제": 1.0, "금융": 1.0, "주식": 1.0, "부동산": 1.0, "금리": 1.0,
    "인플레이션": 1.0, "GDP": 1.0, "수출": 1.0, "수입": 1.0,
    "기업": 0.8, "시장": 0.8, "투자": 0.8, "고용": 0.8, "소비": 0.8,
    "물가": 0.8, "환율": 0.8, "채권": 0.8, "증권": 0.8, "은행": 0.8, "금융권": 0.8,
}
NON_ECONOMY_KEYWORD_PENALTIES = {
    "정치": -0.5, "외교": -0.5, "사회": -0.5, "문화": -0.5,
    "스포츠": -0.5, "연예": -0.5, "교육": -0.5, "과학": -0.5,
    "기술": -0.3, "환경": -0.3, "의료": -0.3, "법률": -0.3,
}

GOOD_QUERIES = [
    "미국 연준의 금리 결정",
    "소비자물가지수 상승률",
    "원자재 가격 변동",
    "상가 임대료 동향",
    "코스피 급락 이유",
    "기업 실적 예측",
    "부동산 가격 동향",
    "무역수지 적자 원인",
    "실업률 증가 배경",
    "에너지 가격 상승 기사",
    "코스닥 투자자 동향",
]

# ─────────────────────────────
# 내부 유틸리티 함수들
# ─────────────────────────────
def normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

def calculate_keyword_score(text: str) -> float:
    score = 0.0
    text = text.lower()
    for keyword, weight in ECONOMY_KEYWORD_WEIGHTS.items():
        if keyword.lower() in text:
            score += weight
    for keyword, penalty in NON_ECONOMY_KEYWORD_PENALTIES.items():
        if keyword.lower() in text:
            score += penalty
    return score

def create_embeddings_batch(client: OpenAI, texts: List[str], model: str, batch_size: int = 10) -> List[List[float]]:
    """텍스트 배치를 임베딩으로 변환"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = client.embeddings.create(
            model=model,
            input=batch
        )
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
        logger.info(f"✅ {min(i+batch_size, len(texts))}/{len(texts)}개 임베딩 완료")
    return embeddings

def load_articles(file_path: str) -> List[Dict[str, Any]]:
    """JSON 파일에서 기사 로드"""
    with open(os.path.join(file_path), 'r', encoding='utf-8') as f:
        return json.load(f)

def create_collection_if_not_exists(q_client: QdrantClient, name: str):
    try:
        q_client.get_collection(collection_name=name)
        logger.info(f"📦 컬렉션 존재 확인됨: {name}")
    except Exception as e:
        logger.info(f"🆕 컬렉션 생성 시도: {name}")
        q_client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        logger.info(f"🆕 컬렉션 생성됨: {name}")

def hybrid_search_with_score(
    vector_store,
    query: str,
    query_embedding: List[float],
    articles_lookup: Dict[str, Dict],
    top_k: int = 5
) -> List[Dict]:
    """
    임베딩 유사도와 키워드 스코어를 결합해 최종 점수(final_score)를 산출한 후,
    최종 점수가 높은 상위 top_k 결과를 반환합니다.
    articles_lookup: { custom_id: article } 형태를 사용합니다.
    """
    results = vector_store.search(
        query_vector=query_embedding,
        top_k=top_k * 2  # 후보군 확장
    )
    scored_results = []
    for result in results:
        doc_id = result['payload']['custom_id']  # "json_order" 대신 "custom_id" 사용
        article = articles_lookup.get(doc_id)
        if not article:
            continue
        keyword_score = max(0.0, calculate_keyword_score(article['content']))
        combined_score = result['score'] * (1 + keyword_score)
        result['keyword_score'] = keyword_score
        result['combined_score'] = combined_score
        result['custom_id'] = doc_id
        scored_results.append(result)
    scores = [r['combined_score'] for r in scored_results]
    if scores:
        min_score, max_score = min(scores), max(scores)
        for r in scored_results:
            r['final_score'] = normalize(r['combined_score'], min_score, max_score)
    else:
        for r in scored_results:
            r['final_score'] = 0.0
    scored_results.sort(key=lambda x: x['final_score'], reverse=True)
    return scored_results[:top_k]

def embed_articles(openai_client: OpenAI, articles: List[Dict]) -> List[List[float]]:
    """기사들을 임베딩합니다."""
    logger.info("🔍 Articles 임베딩 시작...")
    texts = [article['content'] for article in articles]
    embeddings = create_embeddings_batch(openai_client, texts, model="text-embedding-3-small")
    logger.info(f"✅ Articles 임베딩 완료: {len(embeddings)}개")
    return embeddings

def save_embeddings_to_qdrant(
    qdrant_client: QdrantClient,
    articles: List[Dict],
    embeddings: List[List[float]],
    collection_name: str
):
    """임베딩을 Qdrant에 저장합니다."""
    points = []
    for article, embedding in zip(articles, embeddings):
        doc_id = article["custom_id"]
        points.append(
            models.PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "custom_id": doc_id,
                    "title": article.get("title"),
                    "category": article.get("category"),
                    "publication_date": article.get("publication_date"),
                    "keyword_score": calculate_keyword_score(article['content'])
                }
            )
        )
    batch_size = 25
    for i in range(0, len(points), batch_size):
        qdrant_client.upsert(collection_name=collection_name, points=points[i:i+batch_size])
        logger.info(f"✅ {collection_name} 업서트 진행: {min(i+batch_size, len(points))}/{len(points)}")
    logger.info(f"✅ {collection_name} 업서트 완료")

def analyze_search_results(results: List[Dict], articles_lookup: Dict[Any, Dict]) -> Dict:
    """
    검색 결과 분석 함수.
    각 검색 결과의 'custom_id'를 기반으로,
    실제 기사 데이터(articles_lookup)의 'classification' 필드를 확인하여
    경제관련("경제관련")이면 economic, 아니면 non-economic으로 분류합니다.
    """
    analysis = {
        'total_found': len(results),
        'economic_found': 0,
        'non_economic_found': 0,
        'economic_indices': [],
        'non_economic_indices': []
    }
    for result in results:
        doc_id = result['payload']['custom_id']
        article = articles_lookup.get(doc_id, {})
        if article.get('classification') == '경제관련':
            analysis['economic_found'] += 1
            analysis['economic_indices'].append(doc_id)
        else:
            analysis['non_economic_found'] += 1
            analysis['non_economic_indices'].append(doc_id)
    return analysis

def query_articles(
    qdrant_client: QdrantClient,
    openai_client: OpenAI,
    articles_lookup: Dict[str, Dict],
    collection_name: str
) -> Tuple[List[Dict], List[Dict]]:
    """키워드 점수와 벡터 검색을 결합하여 경제/비경제 기사를 분류합니다."""
    logger.info(f"🔍 기사 분류 시작 (총 {len(articles_lookup)}개 기사)")
    
    # 1. 벡터 검색 (이전 코드 유지)
    query_embeddings = create_embeddings_batch(openai_client, GOOD_QUERIES, model="text-embedding-3-small")
    article_scores = {doc_id: [] for doc_id in articles_lookup.keys()}
    vector_store = QdrantVectorStore(qdrant_client, collection_name)
    
    for i, query in enumerate(GOOD_QUERIES):
        logger.info(f"🔍 쿼리 검색: {query}")
        results = hybrid_search_with_score(vector_store, query, query_embeddings[i], articles_lookup, top_k=50)
        for result in results:
            doc_id = result['custom_id']
            score = result['final_score']
            article_scores[doc_id].append(score)
    
    # 2. 키워드 기반 분류 (최종 방식)
    economy_points = []
    others_points = []
    vector_hits = set(doc_id for doc_id, scores in article_scores.items() if scores)
    keyword_matches = set()
    
    for doc_id, article in articles_lookup.items():
        content = article.get('content', '')
        keyword_score = calculate_keyword_score(content)
        
        # 키워드 점수가 0.5 이상이면 경제 관련으로 분류
        is_economic = keyword_score > 0.5
        if is_economic:
            keyword_matches.add(doc_id)
            
        is_vector_hit = doc_id in vector_hits
        
        point = {
            "custom_id": doc_id,
            "title": article.get("title", ""),
            "keyword_score": keyword_score,
            "vector_hit": is_vector_hit,
            "is_economic": is_economic
        }
        
        if is_economic:
            economy_points.append(point)
        else:
            others_points.append(point)
    
    logger.info(f"📊 최종 분류 결과:")
    logger.info(f"- 경제관련 기사: {len(economy_points)}개")
    logger.info(f"- 비경제관련 기사: {len(others_points)}개")
    logger.info(f"- 벡터 검색 히트: {len(vector_hits)}개")
    logger.info(f"- 키워드 매치: {len(keyword_matches)}개")
    logger.info(f"- 벡터만 매치: {len(vector_hits - keyword_matches)}개")
    logger.info(f"- 키워드만 매치: {len(keyword_matches - vector_hits)}개")
    logger.info(f"- 모두 매치: {len(vector_hits & keyword_matches)}개")
    
    return economy_points, others_points

def run_filter_pipeline(
    qdrant_client: QdrantClient,
    openai_client: OpenAI,
    articles: List[Dict],
    collection_economy: str,
    collection_others: str,
    collection_all: str,
):
    """
    전체 필터링 파이프라인 실행 함수.
      1. 기사 데이터를 custom_id 기준 lookup 딕셔너리로 생성합니다.
      2. GOOD_QUERIES 기반 벡터 검색을 통해, 검색 결과에 한 번이라도 등장한 문서를
         예측 경제 기사(economy)로 분류하고, 나머지는 기타(others)로 분류합니다.
      3. 각 문서별 평균 스코어(mean_score)를 계산하여 메타데이터에 저장합니다.
    
    Returns:
        Dict: 평가 결과를 담은 딕셔너리
    """
    logger.info("🚀 필터링 파이프라인 시작")
    logger.info(f"📊 처리할 총 기사 수: {len(articles)}")
    
    # articles_lookup 생성 (키: custom_id)
    articles_lookup = { article["custom_id"]: article for article in articles }
    logger.info(f"✅ 기사 lookup 딕셔너리 생성 완료: {len(articles_lookup)}개")
    
    # GOOD_QUERIES 기반 문서 분류 (이미 저장된 collection_all을 대상으로 검색)
    economy_points, others_points = query_articles(
        qdrant_client,
        openai_client,
        articles_lookup,
        collection_all
    )
    
    # 정확도 평가 (economy_points의 각 항목이 실제로 "경제" 카테고리인지 확인)
    success_count = 0
    fail_count = 0
    
    for point in economy_points:
        custom_id = point["custom_id"]
        # articles_lookup에서 해당 ID의 기사 찾기
        article = articles_lookup.get(custom_id)
        if article and article.get("category") == "경제":
            success_count += 1
        else:
            fail_count += 1
    
    total_count = success_count + fail_count
    accuracy = (success_count / total_count * 100) if total_count > 0 else 0
    
    # 경제인데 비경제로 잘못 분류된 항목(false negative) 평가 추가
    false_negative_count = 0
    false_negatives = []
    total_economy_articles = 0
    
    # 전체 데이터에서 실제 경제 기사 수 확인
    for article in articles:
        if article.get("category") == "경제":
            total_economy_articles += 1
    
    # others_points에서 실제로는 경제 기사인 항목 확인 (false negative)
    for point in others_points:
        custom_id = point["custom_id"]
        article = articles_lookup.get(custom_id)
        if article and article.get("category") == "경제":
            false_negative_count += 1
            false_negatives.append({
                "custom_id": custom_id,
                "title": article.get("title", "제목 없음"),
                "keyword_score": point.get("keyword_score", 0)
            })
    
    false_negative_rate = (false_negative_count / total_economy_articles * 100) if total_economy_articles > 0 else 0
    recall = ((total_economy_articles - false_negative_count) / total_economy_articles * 100) if total_economy_articles > 0 else 0
    
    logger.info("📊 경제 분류 정확도 평가:")
    logger.info(f"- 총 예측 경제 기사: {total_count}개")
    logger.info(f"- 실제 경제 기사(성공): {success_count}개")
    logger.info(f"- 비경제 기사(실패): {fail_count}개")
    logger.info(f"- 분류 정확도: {accuracy:.2f}%")
    logger.info(f"- 실제 경제 기사 총 수: {total_economy_articles}개")
    logger.info(f"- 경제인데 비경제로 오분류(False Negative): {false_negative_count}개")
    logger.info(f"- False Negative 비율: {false_negative_rate:.2f}%")
    logger.info(f"- 경제 기사 검출률(Recall): {recall:.2f}%")
    
    # 경제인데 비경제로 오분류된 사례들 출력
    logger.info("\n📋 경제인데 비경제로 오분류된 사례:")
    for i, fn in enumerate(false_negatives, 1):
        logger.info(f"{i}. ID: {fn['custom_id']}, 키워드 점수: {fn['keyword_score']:.3f}")
        logger.info(f"   제목: {fn['title'][:100]}{'...' if len(fn['title']) > 100 else ''}\n")
    
    logger.info("🎉 Filter pipeline completed successfully.")
    
    # 결과 반환
    return {
        "total_articles": len(articles),
        "total_economy_articles": total_economy_articles,
        "predicted_economy": total_count,
        "true_positive": success_count,
        "false_positive": fail_count,
        "false_negative": false_negative_count,
        "accuracy": accuracy,
        "false_negative_rate": false_negative_rate,
        "recall": recall,
        "precision": (success_count / total_count * 100) if total_count > 0 else 0,
        "f1_score": (2 * recall * (success_count / total_count * 100) / (recall + (success_count / total_count * 100))) if (recall + (success_count / total_count * 100)) > 0 else 0,
        "false_negatives": false_negatives
    }

if __name__ == "__main__":
    qdrant_client = get_qdrant_client()
    openai_client = get_openai_client()
    articles = load_articles('/Users/lee/Desktop/news_parsing/test/llm_output.json')
    
    if articles:
        # 필요한 컬렉션이 존재하지 않으면 생성
        create_collection_if_not_exists(qdrant_client, "collection_all6")
        create_collection_if_not_exists(qdrant_client, "collection_economy6")
        create_collection_if_not_exists(qdrant_client, "collection_others6")
        
        # 1. 먼저 기사 임베딩 및 Qdrant 저장 (라벨과 무관하게)
        embeddings = embed_articles(openai_client, articles)
        save_embeddings_to_qdrant(qdrant_client, articles, embeddings, "collection_all6")
        
        # 2. GOOD_QUERIES를 통한 유사도 검색으로 경제 관련 문서를 후보로 뽑고,
        #    이를 기반으로 각 문서의 평균 스코어(mean_score)를 계산하여 평가
        run_filter_pipeline(qdrant_client, openai_client, articles, "collection_economy6", "collection_others6", "collection_all6")
    else:
        logger.error("❌ 기사 데이터를 불러오는데 실패했습니다.")
