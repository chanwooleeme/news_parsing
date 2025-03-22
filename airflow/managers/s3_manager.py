import boto3
import os
import logging

logger = logging.getLogger(__name__)

class S3Manager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'ap-northeast-2'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'article-crawl-html-storage')
    
    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """파일을 S3에 업로드"""
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            logger.info(f"S3 업로드 성공: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"S3 업로드 실패 ({s3_key}): {e}")
            return False 