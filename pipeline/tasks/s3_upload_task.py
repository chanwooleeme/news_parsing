from common.logger import get_logger
from utils.file import list_files, join_path
import os
import boto3

logger = get_logger(__name__)

def s3_upload_task(html_dir: str):
    s3_client = boto3.client("s3", region_name="ap-northeast-2")
    for filename in list_files(html_dir, extension=".html"):
        html_path = join_path(html_dir, filename)
        s3_client.upload_file(html_path, "news-pipeline-html", html_path)
        logger.info(f"Uploaded {html_path} to s3")
    logger.info(f"Uploaded all HTML files in {html_dir} to s3")