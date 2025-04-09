from fastapi import APIRouter, Depends

from app.models.request_models import ArticleAnalyzeRequest
from app.models.response_models import AnalyzeResponse
from app.services.analyzer_service import AnalyzerService

router = APIRouter()


def get_analyzer_service():
    """AnalyzerService 의존성 주입"""
    return AnalyzerService()


@router.post("", response_model=AnalyzeResponse)
async def analyze_article(
    article: ArticleAnalyzeRequest,
    analyzer_service: AnalyzerService = Depends(get_analyzer_service)
):
    """
    새 기사를 분석하고 관련 기사 찾기
    
    - **content**: 분석할 기사 본문 (필수)
    - **title**: 기사 제목 (선택)
    - **pub_date**: 발행일 (선택)
    - **news_agency**: 언론사 (선택)
    - **top_k**: 찾을 유사 기사 수 (기본값: 5)
    
    Returns:
        관련 기사 목록과 분석 결과
    """
    return await analyzer_service.analyze_article(
        content=article.content,
        title=article.title,
        top_k=article.top_k
    ) 