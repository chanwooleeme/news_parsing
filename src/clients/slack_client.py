# /agentic_retriever/clients/slack_client.py

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from logger import get_logger

logger = get_logger(__name__)

class SlackClient:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def send_message(self, channel: str, text: str) -> bool:
        """슬랙 채널에 메시지 전송"""
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text
            )
            if response["ok"]:
                logger.info(f"✅ Slack 전송 성공 (채널: {channel})")
                return True
            else:
                logger.error(f"❌ Slack 전송 실패: {response['error']}")
                return False
        except SlackApiError as e:
            logger.error(f"❌ Slack API 에러 발생: {e.response['error']}")
            return False
