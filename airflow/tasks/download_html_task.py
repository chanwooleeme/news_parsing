from common.redis_manager import RedisManager
from html_downloader.html_downloader.download import HtmlDownloader, HtmlDownloaderConfig
from airflow.common.file import read_json_file

def download_html_task(html_download_dir: str, rss_source_file: str):
    redis_manager = RedisManager()
    config = HtmlDownloaderConfig(html_download_dir)
    downloader = HtmlDownloader(config, redis_manager)
    rss_source = read_json_file(rss_source_file)
    rss_links_by_publisher = downloader.parse_rss_sources(rss_source)
    downloader.download_articles(rss_links_by_publisher)


if __name__ == "__main__":
    import os
    download_html_task(
        rss_source_file=os.getenv('RSS_SOURCE_FILE', '../data/news_file.json'),
        html_download_dir=os.getenv('HTML_DOWNLOAD_DIR', 'html_files')
    )