from openai import OpenAI
from common.config import OPENAI_API_KEY

def get_openai_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)
