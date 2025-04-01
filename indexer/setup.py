from setuptools import setup, find_packages

setup(
    name="indexer",
    version="0.1.0",
    description="뉴스 기사 임베딩 및 벡터 검색 패키지",
    author="Lee",
    author_email="lee@example.com",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "qdrant-client>=1.6.0",
        "tiktoken>=0.5.0",
        "python-dotenv>=1.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
