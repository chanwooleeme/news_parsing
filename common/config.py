# common/config.py
import os
from dotenv import load_dotenv

# 프로젝트 시작할 때 .env 로딩
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# 환경변수 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")