from setuptools import setup, find_packages

setup(
    name="indexer",
    version="0.1",
    packages=find_packages(exclude=["data", "output", "parquet_files", "tests"]),
    install_requires=[
        "requests",
        "tiktoken",
        "openai",
        "qdrant-client",
    ],
    entry_points={
        "console_scripts": [
            "run-news-pipeline = indexer.pipeline:run_pipeline",
        ],
    },
)
