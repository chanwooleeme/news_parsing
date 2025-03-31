#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML 파서 테스트 스크립트
로컬 및 Docker 환경에서 실행 가능한 간단한 테스트 도구
"""

import os
import sys
from pathlib import Path

# 모듈 임포트 처리
try:
    # 방법 1: 패키지로 설치된 경우
    from html_parser.parser_factory import ParserFactory
    print("✅ 패키지로 설치된 파서를 가져왔습니다.")
except ImportError:
    try:
        # 방법 2: 상대 경로 임포트
        from parser_factory import ParserFactory
        print("✅ 상대 경로로 파서를 가져왔습니다.")
    except ImportError:
        print("❌ 파서 모듈을 찾을 수 없습니다. 올바른 경로에서 실행하고 있는지 확인하세요.")
        sys.exit(1)

# 파서 팩토리 초기화
factory = ParserFactory()

# 지원하는 신문사 출력
newspapers = factory.get_supported_newspapers()
print(f"\n📰 지원하는 신문사 목록 ({len(newspapers)}개):")
for i, newspaper in enumerate(newspapers, 1):
    print(f"  {i}. {newspaper}")

# HTML 디렉토리 확인
html_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "html"
if html_dir.exists():
    print(f"\n📁 HTML 디렉토리 확인: {html_dir}")
    
    # 디렉토리 수 확인
    subdirs = [d for d in html_dir.iterdir() if d.is_dir()]
    print(f"  - {len(subdirs)}개 신문사 디렉토리 발견")
    
    # 각 신문사 디렉토리의 HTML 파일 수 확인
    for subdir in subdirs:
        html_files = list(subdir.glob("*.html"))
        print(f"  - {subdir.name}: {len(html_files)}개 HTML 파일")
        
        # 첫 번째 HTML 파일로 테스트
        if html_files:
            try:
                with open(html_files[0], 'r', encoding='utf-8') as f:
                    html = f.read()
                
                print(f"\n🔍 {subdir.name} 파싱 테스트 중...")
                result = factory.parse(html, subdir.name)
                print(f"  ✅ 파싱 성공:")
                print(f"  - 제목: {result['title'][:50]}..." if len(result['title']) > 50 else f"  - 제목: {result['title']}")
                print(f"  - 작성자: {result['author']}")
                print(f"  - 본문: {result['content'][:100]}..." if len(result['content']) > 100 else f"  - 본문: {result['content']}")
            except Exception as e:
                print(f"  ❌ 파싱 실패: {e}")
else:
    print(f"\n❌ HTML 디렉토리가 없습니다: {html_dir}")

print("\n✅ 테스트가 완료되었습니다.")
