from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router

# 애플리케이션 생성
app = FastAPI(
    title="뉴스 분석 API",
    description="뉴스 기사 분석 및 검색 API",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 추가
app.include_router(api_router)


@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "service": "뉴스 분석 API",
        "version": "1.0.0",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 