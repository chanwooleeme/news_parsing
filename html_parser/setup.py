#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML 파서 패키지 설정 스크립트
"""

from setuptools import setup, find_packages
import os

# README 파일이 있으면 설명으로 사용
readme = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

# 패키지에 필요한 의존성 패키지 정의
requirements = [
    'beautifulsoup4>=4.9.3',
    'lxml>=4.6.3',
    'requests>=2.25.1',
]

# 패키지 설정
setup(
    name='html_parser',
    version='0.1.0',
    description='뉴스 HTML 파서 패키지',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='Admin',
    author_email='admin@example.com',
    packages=find_packages(include=['html_parser', 'html_parser.*', 'parser']),
    package_data={
        'html_parser': ['*.py'],
        'parser': ['*.py'],
    },
    py_modules=['parser_factory', 'test_parser'],
    install_requires=requirements,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'html-parser=test_parser:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
) 