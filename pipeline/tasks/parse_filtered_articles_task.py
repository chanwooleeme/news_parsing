from html_parser.parser_factory import ParserFactory
from utils.file import list_files, list_directories, join_path, splitext_filename, read_text_file, save_dict_as_json
from datasketch import MinHash, MinHashLSH
import hashlib
import logging
import redis
import os

logger = logging.getLogger(__name__)

# Redis 연결 설정
redis_client = redis.Redis(
    host=os.environ.get('REDIS_SERVER_HOST', 'redis'),
    port=os.environ.get('REDIS_SERVER_PORT', 6379),
    db=0
)

def make_minhash(text, num_perm=128, ngram=3):
    """텍스트의 MinHash를 생성합니다."""
    mh = MinHash(num_perm=num_perm)
    for i in range(len(text) - ngram + 1):
        mh.update(text[i:i+ngram].encode('utf8'))
    return mh

def get_minhash_key(title, content):
    """기사의 고유 키를 생성합니다."""
    base = title + content[:200]
    return "minhash:" + hashlib.md5(base.encode()).hexdigest()

def is_duplicate_article(title, content, lsh):
    """기사의 중복 여부를 확인합니다."""
    key = get_minhash_key(title, content)
    
    # Redis에서 중복 체크
    if redis_client.exists(key):
        logger.info(f"Redis에서 중복 기사 발견: {key}")
        return True
    
    # MinHash 생성 및 LSH 쿼리
    mh = make_minhash(title + content[:200])
    matches = lsh.query(mh)
    
    if matches:
        # 중복 기사 발견 시 Redis에 저장 (7일간 유지)
        redis_client.set(key, 1, ex=7 * 86400)
        logger.info(f"LSH에서 중복 기사 발견: {key}")
        return True
    
    # 중복이 아닌 경우 LSH에 추가하고 Redis에 저장
    lsh.insert(key, mh)
    redis_client.set(key, 1, ex=7 * 86400)
    return False

def parse_and_save_articles_task(html_base_dir: str, parsed_base_dir: str) -> None:
    """기사 파싱 후 저장

    Args:
        html_base_dir (str): 기사 HTML 파일 디렉토리
        parsed_base_dir (str): 기사 파싱 결과 저장 디렉토리
    저장 형태:
    {
        "title": "기사 제목",
        "author": "기사 작성자",
        "category": "기사 카테고리",
        "publication_date": "기사 발행일",
        "content": "기사 본문",
        "economic_variables": ["금", "주식", "부동산"]
    }
    """
    parser_factory = ParserFactory()
    lsh = MinHashLSH(threshold=0.8, num_perm=128)  # 유사도 80% 이상을 중복으로 판단

    for newspaper_name in list_directories(html_base_dir):
        newspaper_path = join_path(html_base_dir, newspaper_name)

        for filename in list_files(newspaper_path, extension=".html"):
            html_path = join_path(newspaper_path, filename)

            try:
                html_content = read_text_file(html_path)
                parsed = parser_factory.parse(html_content, newspaper=newspaper_name)
                
                # 중복 체크
                title = parsed.get('title', '')
                content = parsed.get('content', '')
                
                if is_duplicate_article(title, content, lsh):
                    logger.info(f"중복 기사 건너뛰기: {newspaper_name}/{filename}")
                    continue
                
                # 기사 저장
                save_dict_as_json(
                    data=parsed,
                    save_dir=join_path(parsed_base_dir, newspaper_name),
                    filename=splitext_filename(filename)
                )

                logger.info(f"✅ {newspaper_name}/{filename} 파싱 및 저장 완료")
            except Exception as e:
                logger.error(f"❌ {newspaper_name}/{filename} 처리 실패: {e}")
