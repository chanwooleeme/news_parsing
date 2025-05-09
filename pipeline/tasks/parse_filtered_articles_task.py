from html_parser.parser_factory import ParserFactory
from utils.file import list_files, list_directories, join_path, splitext_filename, read_text_file, save_dict_as_json
from datasketch import MinHash, MinHashLSH
import hashlib
import logging
import os
import pickle

logger = logging.getLogger(__name__)

LSH_PATH = "./minhash_lsh.pkl"


def make_minhash(text, num_perm=128, ngram=3):
    mh = MinHash(num_perm=num_perm)
    for i in range(len(text) - ngram + 1):
        mh.update(text[i:i + ngram].encode('utf8'))
    return mh


def get_minhash_key(title, content):
    base = title + content[:200]
    return "minhash:" + hashlib.md5(base.encode()).hexdigest()


def load_lsh(path=LSH_PATH):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return MinHashLSH(threshold=0.8, num_perm=128)


def save_lsh(lsh, path=LSH_PATH):
    with open(path, 'wb') as f:
        pickle.dump(lsh, f)


def is_duplicate_article(title, content, lsh):
    key = get_minhash_key(title, content)
    mh = make_minhash(title + content[:200])

    matches = lsh.query(mh)
    if matches:
        logger.info(f"LSH에서 중복 기사 발견: {key}")
        return True

    lsh.insert(key, mh)
    return False


def parse_and_save_articles_task(html_base_dir: str, parsed_base_dir: str, pickle_path: str) -> None:
    parser_factory = ParserFactory()
    lsh = load_lsh(pickle_path)

    for newspaper_name in list_directories(html_base_dir):
        newspaper_path = join_path(html_base_dir, newspaper_name)

        for filename in list_files(newspaper_path, extension=".html"):
            html_path = join_path(newspaper_path, filename)

            try:
                html_content = read_text_file(html_path)
                parsed = parser_factory.parse(html_content, newspaper=newspaper_name)

                title = parsed.get('title', '')
                content = parsed.get('content', '')

                if is_duplicate_article(title, content, lsh):
                    logger.info(f"중복 기사 건너뛰기: {newspaper_name}/{filename}")
                    continue

                save_dict_as_json(
                    data=parsed,
                    save_dir=join_path(parsed_base_dir, newspaper_name),
                    filename=splitext_filename(filename)
                )

                logger.info(f"✅ {newspaper_name}/{filename} 파싱 및 저장 완료")
            except Exception as e:
                logger.error(f"❌ {newspaper_name}/{filename} 처리 실패: {e}")

    save_lsh(lsh, pickle_path)
