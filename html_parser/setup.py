#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

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
    author='Lee',
    author_email='lee@example.com',
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
) 