from setuptools import setup, find_packages

setup(
    name="rss_feed",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "feedparser==6.0.10",
        "requests==2.31.0",
        "boto3==1.34.34",
        "python-dotenv==1.0.1",
        "redis~=3.2",
    ],
    include_package_data=True,
    author="Your Name",
    author_email="your.email@example.com",
    description="RSS 피드 파싱 및 처리 패키지",
    python_requires=">=3.8",
) 