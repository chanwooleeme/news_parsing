from fastapi import APIRouter, Depends

from app.models.request_models import ArticleUploadRequest
from app.models.response_models import UploadResponse
from app.services.search_service import SearchService

router = APIRouter()


def get_search_service():
    """SearchService 의존성 주입"""
    return SearchService()


@router.post("", response_model=UploadResponse)
async def upload_article(
    article: ArticleUploadRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    새 기사 업로드 엔드포인트
    
    - **title**: 기사 제목 (필수)
    - **content**: 기사 본문 (필수)
    - **pub_date**: 발행일 (필수)
    - **news_agency**: 언론사 (필수)
    - **url**: 원문 URL (선택)
    - **category**: 카테고리 (선택)
    
    Returns:
        업로드 결과 정보
    """
    result = await search_service.upload_article(
        title=article.title,
        content=article.content,
        pub_date=article.pub_date,
        news_agency=article.news_agency,
        url=article.url,
        category=article.category
    )
    
    return UploadResponse(
        success=result["success"],
        article_id=result["article_id"],
        embedding_vector_id=result["embedding_vector_id"],
        timestamp=result["timestamp"]
    ) 