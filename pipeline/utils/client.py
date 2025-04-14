from utils.config import OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from openai import OpenAI
from qdrant_client import QdrantClient
from redis import Redis

def get_openai_client():
    return OpenAI(api_key=OPENAI_API_KEY)

def get_qdrant_client():
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

def get_redis_client():
    return Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD
    )