import boto3
import os
from botocore.exceptions import ClientError
import logging

class S3Manager:
    """AWS S3 상호작용을 관리하는 클래스"""
    
    def __init__(self):
        """
        S3Manager 초기화
        
        Args:
            bucket_name (str): S3 버킷 이름
            region_name (str): AWS 리전 이름
        """
        region_name = os.getenv('AWS_REGION', 'ap-northeast-2')
        print(region_name)
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.bucket_name = os.getenv('AWS_S3_BUCKET')
        
    def upload_file(self, file_path, object_key=None):
        """
        파일을 S3 버킷에 업로드
        
        Args:
            file_path (str): 업로드할 로컬 파일 경로
            object_key (str, optional): S3 객체 키. 지정하지 않으면 파일명 사용
            
        Returns:
            bool: 업로드 성공 시 True, 실패 시 False
        """
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return False
        
        if object_key is None:
            object_key = os.path.basename(file_path)
            
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_key)
            logging.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{object_key}")
            return True
        except ClientError as e:
            logging.error(f"Error uploading file to S3: {e}")
            return False 