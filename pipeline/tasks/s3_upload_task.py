from src.common.logger import get_logger
from utils.file import list_files, join_path, list_directories
import os
import boto3
from botocore.exceptions import ClientError

logger = get_logger(__name__)

def find_html_files_recursive(dir_path):
    """주어진 디렉토리와 모든 하위 디렉토리에서 HTML 파일 찾기"""
    all_html_files = []
    
    # 현재 디렉토리의 HTML 파일
    try:
        current_html_files = [join_path(dir_path, f) for f in list_files(dir_path, extension=".html")]
        all_html_files.extend(current_html_files)
    except Exception as e:
        logger.error(f"현재 디렉토리 {dir_path} 검색 중 오류 발생: {str(e)}")
    
    # 모든 하위 디렉토리에 대해 재귀적으로 파일 찾기
    try:
        subdirs = list_directories(dir_path)
        for subdir in subdirs:
            subdir_path = join_path(dir_path, subdir)
            subdirectory_files = find_html_files_recursive(subdir_path)
            all_html_files.extend(subdirectory_files)
    except Exception as e:
        logger.error(f"하위 디렉토리 검색 중 오류 발생: {str(e)}")
    
    return all_html_files

def s3_upload_task(html_dir: str):
    try:
        logger.info(f"Starting S3 upload task for {html_dir}")
        s3_client = boto3.client("s3", region_name="ap-northeast-2")
        html_dir_with_separator = html_dir if html_dir.endswith(os.sep) else html_dir + os.sep
        
        # 재귀적으로 모든 HTML 파일 찾기
        html_files = find_html_files_recursive(html_dir)
        logger.info(f"Found {len(html_files)} HTML files to upload")
        
        if not html_files:
            logger.warning(f"No HTML files found in {html_dir}")
            return
            
        for html_path in html_files:
            try:
                # html_dir 경로를 제외한 상대 경로를 S3 키로 사용
                s3_key = html_path.replace(html_dir_with_separator, "")
                logger.info(f"Uploading {html_path} to S3 bucket with key {s3_key}")
                s3_client.upload_file(html_path, "article-crawl-html-storage", s3_key)
                logger.info(f"Successfully uploaded {html_path} to s3 with key {s3_key}")
            except ClientError as e:
                logger.error(f"Failed to upload {html_path}: {str(e)}")
                continue
            except FileNotFoundError:
                logger.error(f"File not found: {html_path}")
                continue
                
        logger.info(f"Uploaded all HTML files in {html_dir} to s3")
    except Exception as e:
        logger.error(f"Error in S3 upload task: {str(e)}")
        raise


if __name__ == "__main__":
    # 환경 변수에서 HTML 디렉토리 경로를 가져오거나 기본값 사용
    html_dir = os.getenv("HTML_DOWNLOAD_DIR", "data/html_files")
    s3_upload_task(html_dir=html_dir)