# /agentic_retriever/slack/slack_client.py

import requests

class SlackClient:
    def __init__(self, slack_token: str):
        self.slack_token = slack_token
        self.slack_api_url = "https://slack.com/api/chat.postMessage"

    def send_message(self, channel: str, text: str) -> bool:
        """Slack 채널에 메시지를 전송합니다."""
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "channel": channel,
            "text": text
        }

        response = requests.post(self.slack_api_url, headers=headers, json=payload)

        if response.status_code == 200 and response.json().get("ok"):
            print(f"[Slack] 메시지 전송 성공: {channel}")
            return True
        else:
            print(f"[Slack] 메시지 전송 실패: {response.text}")
            return False
