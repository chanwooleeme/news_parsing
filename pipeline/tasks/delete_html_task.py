from common.logger import get_logger
from utils.file import list_files, join_path
import os

logger = get_logger(__name__)

def delete_html_task(html_dir: str):
    for filename in list_files(html_dir, extension=".html"):
        html_path = join_path(html_dir, filename)
        os.remove(html_path)
        logger.info(f"Deleted {html_path}")
    
    logger.info(f"Deleted all HTML files in {html_dir}")

if __name__ == "__main__":
    delete_html_task(html_dir=os.getenv("HTML_DOWNLOAD_DIR"))