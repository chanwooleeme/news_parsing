import os
from dotenv import load_dotenv

# 환경 변수 확인
IS_DOCKER = os.getenv('IS_DOCKER', 'false').lower() == 'true'

# 로컬 환경에서만 .env 로드
if not IS_DOCKER:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Qdrant 설정
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "economy-articles")

# Redis 설정
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
