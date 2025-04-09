from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str = Field(..., description="서버 상태")
    version: str = Field(..., description="API 버전")
    timestamp: datetime = Field(..., description="현재 시간")


class RelatedArticle(BaseModel):
    """유사 기사 정보"""
    title: str = Field(..., description="기사 제목")
    score: float = Field(..., description="유사도 점수")
    relationship: Optional[str] = Field(None, description="관계 (포함/변경/확장/모순/무관)")
    reason: Optional[str] = Field(None, description="관계 설명")
    news_agency: Optional[str] = Field(None, description="언론사")
    pub_date: Optional[str] = Field(None, description="발행일")
    url: Optional[str] = Field(None, description="원문 URL")


class AnalyzeResponse(BaseModel):
    """분석 결과 응답 모델"""
    related_articles: List[RelatedArticle] = Field(..., description="관련 기사 목록")
    analysis_time: float = Field(..., description="분석 소요 시간(초)")
    timestamp: datetime = Field(..., description="분석 시간")


class SearchResultItem(BaseModel):
    """검색 결과 아이템"""
    title: str = Field(..., description="기사 제목")
    content_preview: str = Field(..., description="본문 미리보기")
    score: float = Field(..., description="검색 점수")
    news_agency: str = Field(..., description="언론사")
    pub_date: str = Field(..., description="발행일")
    url: Optional[str] = Field(None, description="원문 URL")


class SearchResponse(BaseModel):
    """검색 결과 응답 모델"""
    results: List[SearchResultItem] = Field(..., description="검색 결과")
    total_count: int = Field(..., description="총 결과 수")
    query_time: float = Field(..., description="검색 소요 시간(초)")


class SummaryItem(BaseModel):
    """요약 아이템"""
    title: str = Field(..., description="요약 제목")
    summary: str = Field(..., description="요약 내용")
    news_agencies: List[str] = Field(..., description="포함된 언론사")
    article_count: int = Field(..., description="요약에 포함된 기사 수")
    pub_date: str = Field(..., description="발행일")


class SummaryResponse(BaseModel):
    """요약 응답 모델"""
    summaries: List[SummaryItem] = Field(..., description="요약 목록")
    generation_time: float = Field(..., description="요약 생성 소요 시간(초)")


class UploadResponse(BaseModel):
    """업로드 응답 모델"""
    success: bool = Field(..., description="업로드 성공 여부")
    article_id: str = Field(..., description="생성된 기사 ID")
    embedding_vector_id: str = Field(..., description="벡터 ID")
    timestamp: datetime = Field(..., description="업로드 시간") 