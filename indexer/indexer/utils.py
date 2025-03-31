import os
import json
import glob
import logging
import sys
from datetime import datetime
from typing import List, Dict

import tiktoken  # OpenAI tokenizer

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 토큰 처리 함수들
def get_token_length(text: str, model: str = "text-embedding-3-large") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def truncate_to_token_limit(text: str, max_tokens: int = 8191, model: str = "text-embedding-3-large") -> str:
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    return enc.decode(tokens[:max_tokens])


def get_html_files(directory: str) -> List[str]:
    """HTML 파일 목록 반환"""
    return sorted(glob.glob(os.path.join(directory, '**', '*.html'), recursive=True))


def load_parser_factory():
    """ParserFactory 로딩"""
    # 파이썬 경로에 상위 디렉토리 추가 (로컬 환경에서의 실행을 위해)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
        
    try:
        # 첫 번째 시도: 패키지로 설치된 경우
        from html_parser.parser_factory import ParserFactory
        logging.info("html_parser 패키지에서 ParserFactory를 불러왔습니다.")
    except ImportError:
        try:
            # 두 번째 시도: 직접 경로 지정
            sys.path.append(os.path.join(parent_dir, 'html_parser'))
            from parser_factory import ParserFactory
            logging.info("상대 경로에서 ParserFactory를 불러왔습니다.")
        except ImportError as e:
            logging.error(f"ParserFactory를 불러올 수 없습니다: {e}")
            logging.error(f"현재 sys.path: {sys.path}")
            raise ImportError("html_parser가 설치되어 있는지 또는 경로가 올바른지 확인하세요.")
    
    return ParserFactory()


def parse_articles_by_newspaper(factory, html_files: List[str], html_dir: str) -> Dict[str, List[Dict]]:
    """신문사별로 기사 파싱"""
    newspaper_groups: Dict[str, List[Dict]] = {}
    supported_newspapers = factory.get_supported_newspapers()
    total_count = 0
    success_count = 0

    for html_file in html_files:
        filename = os.path.basename(html_file)
        total_count += 1
        try:
            relative_path = os.path.relpath(html_file, html_dir)
            parts = relative_path.split(os.sep)
            newspaper = parts[0]

            if newspaper not in supported_newspapers:
                logging.warning(f"지원하지 않는 신문사 {newspaper}의 파일 건너뜀: {html_file}")
                continue

            with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()

            parsed = factory.parse(html_content, newspaper)

            content = parsed["content"]
            token_length = get_token_length(content)
            if token_length > 8191:
                logging.warning(f"{filename} 본문이 {token_length} 토큰으로 너무 김. 자릅니다.")
                content = truncate_to_token_limit(content)

            success_count += 1

            article = {
                "file_id": filename,
                "custom_id": filename.replace(".html", ""),
                "newspaper": newspaper,
                "title": parsed["title"],
                "author": parsed["author"],
                "timestamp": parsed["publication_date"],
                "content": content,
                "category": None
            }

            newspaper_groups.setdefault(newspaper, []).append(article)

        except Exception as e:
            logging.error(f"[ERROR] {filename} 처리 실패: {e}")
            continue

    if total_count > 0:
        logging.info(f"총 {total_count}개 중 {success_count}개 파싱 성공 ({success_count/total_count*100:.1f}%)")
    return newspaper_groups


def save_batch_files(newspaper_groups: Dict[str, List[Dict]], output_dir: str) -> List[str]:
    """신문사별 배치 파일 저장"""
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
    saved_files = []

    for newspaper, articles in newspaper_groups.items():
        if not articles:
            logging.warning(f"신문사 '{newspaper}'의 기사가 없어 파일 생성 건너뜀")
            continue

        jsonl_lines = []
        metadata_list = []

        for idx, article in enumerate(articles):
            jsonl_lines.append(json.dumps({
                "custom_id": article["custom_id"],
                "method": "POST",
                "url": "/v1/embeddings",
                "body": {
                    "model": "text-embedding-3-large",
                    "input": article["content"]
                }
            }, ensure_ascii=False))

            metadata_list.append({
                "index": idx,
                "custom_id": article["custom_id"],
                "id": article["custom_id"],
                "title": article["title"],
                "author": article["author"],
                "timestamp": article["timestamp"],
                "filename": article["file_id"],
                "newspaper": article["newspaper"],
                "category": article["category"]
            })

        jsonl_path = os.path.join(output_dir, f"openai_batch_{newspaper}_embedding_{timestamp_str}.jsonl")
        metadata_path = os.path.join(output_dir, f"openai_batch_{newspaper}_metadata_{timestamp_str}.json")

        with open(jsonl_path, "w", encoding="utf-8") as f:
            f.write("\n".join(jsonl_lines))

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=2)

        saved_files.extend([jsonl_path, metadata_path])
        logging.info(f"저장됨: {jsonl_path} ({len(jsonl_lines)}개 항목)")

    return saved_files
