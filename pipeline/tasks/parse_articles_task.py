from html_parser.parser_factory import ParserFactory
from utils.file import list_files, list_directories, join_path, splitext_filename, read_text_file, save_dict_as_json

def parse_and_save_articles_task(html_base_dir: str, parsed_base_dir: str) -> None:
    parser_factory = ParserFactory()

    for newspaper_name in list_directories(html_base_dir):
        newspaper_path = join_path(html_base_dir, newspaper_name)

        for filename in list_files(newspaper_path, extension=".html"):
            html_path = join_path(newspaper_path, filename)

            try:
                html_content = read_text_file(html_path)
                parsed = parser_factory.parse(html_content, newspaper=newspaper_name)

                save_dict_as_json(
                    data=parsed,
                    save_dir=join_path(parsed_base_dir, newspaper_name),
                    filename=splitext_filename(filename)
                )

                print(f"✅ {newspaper_name}/{filename} 파싱 및 저장 완료")
            except Exception as e:
                print(f"❌ {newspaper_name}/{filename} 처리 실패: {e}")

if __name__ == "__main__":
    import os
    parse_and_save_articles_task(
        html_base_dir=os.getenv('HTML_DOWNLOAD_DIR', 'html_files'),
        parsed_base_dir=os.getenv('PARSED_ARTICLES_DIR', 'parsed_articles')
    )
    