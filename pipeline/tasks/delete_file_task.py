from logger import get_logger
from utils.file import list_files, list_directories, join_path
import os
from typing import List

logger = get_logger(__name__)

def delete_files_in_directory(directory: str, extension: str) -> None:
    """주어진 디렉토리에서 특정 확장자를 가진 파일들을 삭제"""
    for filename in list_files(directory, extension=extension):
        file_path = join_path(directory, filename)
        try:
            os.remove(file_path)
            logger.info(f"Deleted {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")

def delete_files_recursively(base_dir: str, extension: str) -> None:
    """재귀적으로 디렉토리를 순회하며 파일 삭제"""
    # 루트 디렉토리에서 직접 파일 삭제
    delete_files_in_directory(base_dir, extension)
    
    # 신문사 디렉토리 순회
    for newspaper in list_directories(base_dir):
        newspaper_dir = join_path(base_dir, newspaper)
        delete_files_in_directory(newspaper_dir, extension)

def delete_file_task(html_dir: str, parsed_news_dir: str) -> None:
    """HTML과 파싱된 뉴스 파일 삭제"""
    # HTML 파일 삭제
    delete_files_recursively(html_dir, ".html")
    
    # 파싱된 뉴스 파일 삭제
    delete_files_recursively(parsed_news_dir, ".json")
    
    logger.info(f"정리 완료: {html_dir}, {parsed_news_dir}")

if __name__ == "__main__":
    delete_file_task(
        "/Users/lee/Desktop/news_parsing/pipeline/tasks/html_files",
        "/Users/lee/Desktop/news_parsing/pipeline/tasks/parsed_articles"
    )