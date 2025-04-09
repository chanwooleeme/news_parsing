from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date


class ArticleAnalyzeRequest(BaseModel):
    """새 기사 분석 요청 모델"""
    content: str = Field(..., description="분석할 기사 본문")
    title: Optional[str] = Field(None, description="기사 제목")
    pub_date: Optional[str] = Field(None, description="발행일")
    news_agency: Optional[str] = Field(None, description="언론사")
    top_k: Optional[int] = Field(5, description="검색할 유사 기사 수")


class SearchRequest(BaseModel):
    """기사 검색 요청 모델"""
    query: str = Field(..., description="검색 쿼리")
    top_k: Optional[int] = Field(10, description="검색 결과 수")
    filter_date_from: Optional[date] = Field(None, description="검색 시작일")
    filter_date_to: Optional[date] = Field(None, description="검색 종료일")
    filter_news_agency: Optional[List[str]] = Field(None, description="검색할 언론사 필터")


class SummaryRequest(BaseModel):
    """최근 기사 요약 요청 모델"""
    days: Optional[int] = Field(1, description="몇 일 전 기사를 요약할지")
    category: Optional[str] = Field(None, description="카테고리")
    news_agency: Optional[str] = Field(None, description="언론사")


class ArticleUploadRequest(BaseModel):
    """기사 업로드 요청 모델"""
    title: str = Field(..., description="기사 제목")
    content: str = Field(..., description="기사 본문")
    pub_date: str = Field(..., description="발행일")
    news_agency: str = Field(..., description="언론사")
    url: Optional[str] = Field(None, description="원문 URL")
    category: Optional[str] = Field(None, description="카테고리") 