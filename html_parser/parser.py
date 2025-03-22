import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import boto3

# 환경변수 (ECS 태스크의 컨테이너 환경변수로 설정)
SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET", "article-crawl-html-storage")
CATEGORY_FOLDER = os.environ.get("CATEGORY_FOLDER", "culture")  # 예: "news/html/"
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET", "article-crawl-parquet-storage")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "5"))  # 한 번에 처리할 파일 개수

def extract_date_components(published_time_str):
    """published_time 문자열(ISO 형식)에서 연도, 월, 일을 추출합니다."""
    try:
        dt = datetime.fromisoformat(published_time_str)
        return dt.year, dt.month, dt.day
    except Exception as e:
        return None, None, None

def extract_article_data(html_content):
    """HTML 콘텐츠에서 핵심 기사 데이터를 추출합니다."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 아티클 ID
    article_id = None
    id_tag = soup.find('meta', property='article_id')
    if id_tag and id_tag.get('content'):
        article_id = id_tag['content'].strip()
    
    # 제목
    title = None
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    
    # 작성자 (후행 "기자" 제거)
    author = None
    author_tag = soup.find('meta', property='article:author')
    if author_tag and author_tag.get('content'):
        author = author_tag['content'].strip()
        author = re.sub(r'\s*기자$', '', author)
    
    # 카테고리
    category = None
    category_tag = soup.find('meta', property='article:section')
    if category_tag and category_tag.get('content'):
        category = category_tag['content'].strip()
    
    # 본문: <p> 태그 중 class에 "content_text" 포함된 태그
    paragraphs = soup.find_all('p', class_=lambda c: c and 'content_text' in c)
    content_text = '\n'.join([p.get_text(strip=True) for p in paragraphs]) if paragraphs else None
    if content_text:
        # 개행문자 모두 제거
        content_text = content_text.replace("\n", " ").strip()
        # 길이가 6000자 이상이면 <meta name="description"> 태그의 내용을 우선 사용 (없으면 6000자로 자름)
        if len(content_text) > 6000:
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag and desc_tag.get('content'):
                content_text = desc_tag['content'].strip()
            else:
                content_text = content_text[:6000]
    
    # URL
    url = None
    url_tag = soup.find('meta', property='og:url')
    if url_tag and url_tag.get('content'):
        url = url_tag['content'].strip()
    
    # 발행일
    published_time = None
    time_tag = soup.find('meta', property='article:published_time')
    if time_tag and time_tag.get('content'):
        published_time = time_tag['content'].strip()
    
    year, month, day = extract_date_components(published_time) if published_time else (None, None, None)
    
    return {
        "article_id": article_id,
        "title": title,
        "author": author,
        "category": category,
        "content_text": content_text,
        "url": url,
        "published_time": published_time,
        "year": year,
        "month": month,
        "day": day
    }

def process_s3_file(s3_client, bucket, key):
    """S3의 단일 HTML 파일을 처리하여 데이터를 추출합니다."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        html_content = response['Body'].read().decode('utf-8', errors='ignore')
        return extract_article_data(html_content)
    except Exception as e:
        print(f"파일 처리 오류 ({key}): {e}")
        return None

def list_s3_objects(s3_client, bucket, prefix):
    """S3 버킷에서 주어진 prefix 하의 모든 객체(Key)를 반환합니다."""
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
    for page in page_iterator:
        for obj in page.get('Contents', []):
            yield obj['Key']

def save_to_parquet(records, output_file):
    """추출된 데이터를 Parquet 파일로 저장합니다."""
    df = pd.DataFrame(records)
    df.to_parquet(output_file, index=False)
    print(f"로컬에 {output_file}로 저장되었습니다.")

def upload_file_to_s3(s3_client, local_file, bucket, key):
    """로컬 파일을 S3에 업로드합니다."""
    try:
        s3_client.upload_file(local_file, bucket, key)
        print(f"파일이 S3://{bucket}/{key} 에 업로드되었습니다.")
    except Exception as e:
        print(f"S3 업로드 오류: {e}")

def main():
    s3_client = boto3.client('s3', region_name="ap-northeast-2")
    
    # S3에서 객체 리스트 가져오기 (최대 10만개까지)
    all_keys = list(list_s3_objects(s3_client, SOURCE_BUCKET, CATEGORY_FOLDER))
    print(f"총 {len(all_keys)}개의 파일이 S3에서 검색되었습니다.")
    
    records = []
    batch_count = 0
    processed_count = 0
    local_parquet_file = 'articles_partial.parquet'
    
    # 키 목록을 배치 단위로 처리
    for key in all_keys:
        record = process_s3_file(s3_client, SOURCE_BUCKET, key)
        processed_count += 1
        # content_text가 없는 경우는 스킵
        if record and record.get("content_text"):
            records.append(record)
        else:
            print(f"내용 누락 파일 스킵: {key}")
        
        # 배치 처리: BATCH_SIZE마다 업로드 진행
        if processed_count % BATCH_SIZE == 0:
            batch_count += 1
            print(f"[배치 {batch_count}] {processed_count}개 파일 처리 완료. (현재 누적 레코드: {len(records)} 건)")
            # 현재까지의 기록을 Parquet 파일로 저장하고 S3에 업로드
            save_to_parquet(records, local_parquet_file)
            # S3 업로드 시 현재 카테고리 폴더를 사용
            upload_file_to_s3(s3_client, local_parquet_file, OUTPUT_BUCKET, CATEGORY_FOLDER + "/articles.parquet")
    
    # 남은 파일 처리 후, 최종 업로드 (마지막 배치가 BATCH_SIZE 미만일 경우)
    if processed_count % BATCH_SIZE != 0:
        print(f"[최종 배치] {processed_count}개 파일 처리 완료. (최종 누적 레코드: {len(records)} 건)")
        save_to_parquet(records, local_parquet_file)
        upload_file_to_s3(s3_client, local_parquet_file, OUTPUT_BUCKET, CATEGORY_FOLDER + "/articles.parquet")
    
    # 로컬 파일 삭제 (원하는 경우)
    try:
        os.remove(local_parquet_file)
        print(f"로컬 파일 {local_parquet_file} 삭제 완료.")
    except Exception as e:
        print(f"로컬 파일 삭제 오류: {e}")

if __name__ == "__main__":
    main()
