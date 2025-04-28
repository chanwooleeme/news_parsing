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
