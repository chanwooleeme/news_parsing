from fastapi import APIRouter, Depends

from app.models.request_models import SearchRequest
from app.models.response_models import SearchResponse
from app.services.search_service import SearchService

router = APIRouter()


def get_search_service():
    """SearchService 의존성 주입"""
    return SearchService()


@router.post("", response_model=SearchResponse)
async def search_articles(
    search_req: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    기사 검색 엔드포인트
    
    - **query**: 검색 쿼리 (필수)
    - **top_k**: 검색 결과 수 (기본값: 10)
    - **filter_date_from**: 시작일 필터 (선택)
    - **filter_date_to**: 종료일 필터 (선택)
    - **filter_news_agency**: 언론사 필터 (선택)
    
    Returns:
        검색 결과 목록
    """
    return await search_service.search_articles(
        query=search_req.query,
        top_k=search_req.top_k,
        filter_date_from=search_req.filter_date_from,
        filter_date_to=search_req.filter_date_to,
        filter_news_agency=search_req.filter_news_agency
    ) 