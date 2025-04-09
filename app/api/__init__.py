from fastapi import APIRouter

from app.api.endpoints import health, analyze, search, summary, upload

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(summary.router, prefix="/recent-summaries", tags=["summary"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"]) 