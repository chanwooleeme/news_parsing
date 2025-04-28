from utils.file import read_json_file
from html_downloader.html_downloader import HtmlDownloader, HtmlDownloaderConfig
from utils.client import get_redis_client

def download_html_task(html_download_dir: str, rss_source_file: str):
    redis_client = get_redis_client()
    config = HtmlDownloaderConfig(html_download_dir, redis_client=redis_client)
    downloader = HtmlDownloader(config)
    rss_source = read_json_file(rss_source_file)
    rss_links_by_publisher = downloader.parse_rss_sources(rss_source)
    result = downloader.download_articles(rss_links_by_publisher)
    return result


if __name__ == "__main__":
    import os
    from logger import get_logger
    from utils.client import get_redis_client
    logger = get_logger(__name__)
    logger.info("Downloading HTML files...")
    redis_client = get_redis_client()
    download_html_task(
        rss_source_file=os.getenv('RSS_SOURCE_FILE', '/Users/lee/Desktop/news_parsing/data/economy.json'),
        html_download_dir=os.getenv('HTML_DOWNLOAD_DIR', 'html_files'),
        redis_client=redis_client
    )