from fastapi import APIRouter, Depends

from app.models.request_models import SummaryRequest
from app.models.response_models import SummaryResponse
from app.services.summary_service import SummaryService

router = APIRouter()


def get_summary_service():
    """SummaryService 의존성 주입"""
    return SummaryService()


@router.get("", response_model=SummaryResponse)
async def get_recent_summaries(
    days: int = 1,
    category: str = None,
    news_agency: str = None,
    summary_service: SummaryService = Depends(get_summary_service)
):
    """
    최근 기사 요약 조회 엔드포인트
    
    - **days**: 몇 일 전 기사를 요약할지 (기본값: 1)
    - **category**: 카테고리 필터 (선택)
    - **news_agency**: 언론사 필터 (선택)
    
    Returns:
        최근 기사 요약 목록
    """
    return await summary_service.get_recent_summaries(
        days=days,
        category=category,
        news_agency=news_agency
    ) 