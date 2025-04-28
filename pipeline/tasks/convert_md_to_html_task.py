#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import markdown
from logger import get_logger
import os

logger = get_logger(__name__)

def convert_md_to_html(md_file_path: str, html_file_path: str):
    """
    마크다운 파일을 HTML로 변환
    
    Args:
        md_file_path (str): 입력 마크다운 파일 경로
        html_file_path (str): 출력 HTML 파일 경로
        
    Returns:
        str: 생성된 HTML 파일 경로
    """
    logger.info(f"🔄 마크다운을 HTML로 변환 시작: {md_file_path} -> {html_file_path}")
    
    try:
        # 마크다운 파일 읽기
        with open(md_file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        # 마크다운을 HTML로 변환
        body_html = markdown.markdown(md_content, extensions=['extra', 'nl2br'])
        
        # 완전한 HTML 문서 작성
        full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>데일리 경제 리포트</title>
    <style>
        body {{
            max-width: 800px;
            margin: 40px auto;
            font-family: 'Arial', 'Helvetica', sans-serif;
            line-height: 1.6;
            padding: 0 20px;
            background-color: #f9f9f9;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        code {{
            background-color: #f0f0f0;
            padding: 2px 4px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
{body_html}
</body>
</html>"""
        
        # 출력 디렉토리가 없으면 생성
        output_dir = os.path.dirname(html_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # HTML 파일 작성
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        
        logger.info(f"✅ HTML 변환 완료: {html_file_path}")
        return html_file_path
        
    except Exception as e:
        logger.error(f"❌ HTML 변환 실패: {str(e)}")
        raise 