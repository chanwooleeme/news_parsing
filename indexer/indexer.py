"""
뉴스 기사 임베딩 및 벡터 저장소 처리 모듈
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import glob

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from html_parser import ParserFactory

# 로깅 설정 향상
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("indexer")

class NewsIndexer:
    """뉴스 기사 임베딩 및 벡터 저장소 처리 클래스"""
    
    def __init__(self):
        """환경 변수에서 설정을 로드하고 클라이언트 초기화"""
        # 환경 변수 로드
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.qdrant_host = os.getenv("QDRANT_HOST")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.html_dir = os.getenv("RSS_FEED_HTML_DIR", os.path.join(os.getcwd(), "data", "html"))
        self.collection_name = os.getenv("QDRANT_COLLECTION", "news_articles")
        
        # 환경 변수 로깅
        logger.info(f"NewsIndexer 초기화 - HTML 디렉토리: {self.html_dir}")
        logger.info(f"NewsIndexer 초기화 - Qdrant 호스트: {self.qdrant_host}")
        logger.info(f"NewsIndexer 초기화 - 컬렉션 이름: {self.collection_name}")
        
        if not all([self.openai_api_key, self.qdrant_host, self.qdrant_api_key]):
            logger.error("필수 환경 변수가 설정되지 않았습니다: OPENAI_API_KEY, QDRANT_HOST, QDRANT_API_KEY")
            raise ValueError("필수 환경 변수가 설정되지 않았습니다: OPENAI_API_KEY, QDRANT_HOST, QDRANT_API_KEY")
        
        # 클라이언트 초기화
        logger.info("OpenAI 클라이언트 초기화 중...")
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Qdrant 클라이언트 초기화 (URL 또는 host/port 방식으로)
        logger.info("Qdrant 클라이언트 초기화 중...")
        if self.qdrant_host.startswith(('http://', 'https://')):
            logger.info(f"URL 모드로 Qdrant 연결 중: {self.qdrant_host}")
            self.qdrant_client = QdrantClient(
                url=self.qdrant_host,
                api_key=self.qdrant_api_key
            )
        else:
            logger.info(f"호스트 모드로 Qdrant 연결 중: {self.qdrant_host}")
            self.qdrant_client = QdrantClient(
                host=self.qdrant_host,
                api_key=self.qdrant_api_key
            )
        
        # 파서 팩토리 초기화
        logger.info("파서 팩토리 초기화 중...")
        self.parser_factory = ParserFactory()
        
        # 컬렉션 생성 (없는 경우)
        self._init_collection()
    
    def _init_collection(self) -> None:
        """Qdrant 컬렉션 초기화"""
        try:
            logger.info(f"컬렉션 확인 중: {self.collection_name}")
            collections = self.qdrant_client.get_collections().collections
            exists = any(col.name == self.collection_name for col in collections)
            
            if not exists:
                logger.info(f"컬렉션이 존재하지 않음, 새로 생성: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
                logger.info(f"컬렉션 생성 완료: {self.collection_name}")
            else:
                logger.info(f"기존 컬렉션 사용: {self.collection_name}")
        except Exception as e:
            logger.error(f"컬렉션 초기화 중 오류 발생: {e}", exc_info=True)
            raise
    
    def _get_html_files(self) -> List[str]:
        """HTML 파일 목록 가져오기"""
        logger.info(f"HTML 파일 검색 중: {self.html_dir}")
        html_pattern = os.path.join(self.html_dir, "**", "*.html")
        files = glob.glob(html_pattern, recursive=True)
        logger.info(f"HTML 파일 {len(files)}개 발견")
        return files
    
    def _get_html_content(self, file_path: str) -> str:
        """HTML 파일 내용 로드"""
        logger.info(f"HTML 파일 읽기: {file_path}")
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
            decoded = content.decode('utf-8', errors='replace')
            logger.info(f"HTML 파일 읽기 성공: {file_path} ({len(decoded)} 바이트)")
            return decoded
        except Exception as e:
            logger.error(f"HTML 파일 읽기 중 오류 발생: {file_path} - {e}", exc_info=True)
            return None
    
    def _create_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        logger.info(f"임베딩 생성 중: 텍스트 길이 {len(text)} 자")
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response.data[0].embedding
            logger.info(f"임베딩 생성 완료: 차원 {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"임베딩 생성 중 오류 발생: {e}", exc_info=True)
            raise
    
    def process_articles(self, limit: Optional[int] = None) -> Tuple[int, List[Dict[str, Any]]]:
        """HTML 파일을 파싱하고 임베딩 생성 후 Qdrant에 저장"""
        logger.info(f"기사 처리 시작 (최대 {limit if limit else '무제한'}개)")
        
        html_files = self._get_html_files()
        if limit:
            logger.info(f"처리 제한: {limit}개 파일")
            html_files = html_files[:limit]
        
        if not html_files:
            logger.warning(f"처리할 HTML 파일이 없습니다: {self.html_dir}")
            return 0, []
        
        processed_articles = []
        processed_count = 0
        error_count = 0
        
        for file_path in html_files:
            try:
                # 파일 경로에서 신문사 이름 추출
                newspaper = Path(file_path).parent.name
                logger.info(f"파일 처리 중 ({processed_count+1}/{len(html_files)}): {file_path} (신문사: {newspaper})")
                
                # HTML 내용 읽기
                html_content = self._get_html_content(file_path)
                
                if not html_content:
                    logger.warning(f"HTML 내용이 비어있습니다: {file_path}")
                    error_count += 1
                    continue
                
                # HTML 파싱
                try:
                    logger.info(f"HTML 파싱 중: {newspaper}")
                    article = self.parser_factory.parse(html_content, newspaper)
                    
                    if not article or not article.get("content"):
                        logger.warning(f"내용이 비어있는 기사: {file_path}")
                        error_count += 1
                        continue
                    
                    logger.info(f"파싱 성공: {article.get('title', '제목 없음')[:30]}...")
                except ValueError as e:
                    logger.warning(f"파싱 오류 (신문사 지원 안함): {e}")
                    error_count += 1
                    continue
                except Exception as e:
                    logger.error(f"파싱 오류: {e}", exc_info=True)
                    error_count += 1
                    continue
                
                # 임베딩 생성
                logger.info(f"임베딩 생성 중: 콘텐츠 길이 {len(article['content'])} 자")
                embedding = self._create_embedding(article["content"])
                
                # 메타데이터 준비
                metadata = {
                    "newspaper": newspaper,
                    "title": article.get("title", ""),
                    "author": article.get("author", ""),
                    "category": article.get("category", ""),
                    "timestamp": article.get("timestamp", "")
                }
                logger.info(f"메타데이터 준비 완료: {metadata['title']}")
                
                # Qdrant에 저장
                logger.info(f"Qdrant에 저장 중: ID {article['custom_id']}, 컬렉션 {self.collection_name}")
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[{
                        "id": article["custom_id"],
                        "payload": {
                            "content": article["content"],
                            **metadata
                        },
                        "vector": embedding
                    }]
                )
                logger.info("Qdrant에 저장 성공")
                
                processed_articles.append({
                    "file_path": file_path,
                    "metadata": metadata
                })
                
                processed_count += 1
                logger.info(f"처리 완료 ({processed_count}/{len(html_files)}): {metadata['title']} ({newspaper})")
                
            except Exception as e:
                logger.error(f"파일 처리 중 오류 발생 ({file_path}): {e}", exc_info=True)
                error_count += 1
                continue
        
        logger.info(f"처리 통계: 총 {len(html_files)}개 중 {processed_count}개 성공, {error_count}개 실패")
        return processed_count, processed_articles
        
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        텍스트 쿼리로 기사를 검색합니다.
        
        Args:
            query: 검색 쿼리
            limit: 반환할 최대 결과 수
            
        Returns:
            검색 결과 목록
        """
        logger.info(f"검색 요청: 쿼리='{query}', 제한={limit}")
        try:
            # 쿼리 임베딩 생성
            logger.info("쿼리 임베딩 생성 중...")
            query_embedding = self._create_embedding(query)
            
            # Qdrant에서 검색 실행
            logger.info(f"Qdrant에서 검색 실행 중: 컬렉션={self.collection_name}, 제한={limit}")
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            logger.info(f"검색 결과: {len(search_results)}개 항목")
            
            # 결과 변환
            results = []
            for i, result in enumerate(search_results):
                # 메타데이터 추출
                payload = result.payload
                metadata = {
                    "title": payload.get("title", ""),
                    "newspaper": payload.get("newspaper", ""),
                    "author": payload.get("author", ""),
                    "category": payload.get("category", ""),
                    "url": payload.get("url", ""),
                    "timestamp": payload.get("timestamp", "")
                }
                
                # 결과 구성
                results.append({
                    "content": payload.get("content", ""),
                    "metadata": metadata,
                    "score": result.score,
                    "id": result.id
                })
                logger.info(f"결과 #{i+1}: score={result.score:.4f}, title='{metadata['title'][:30]}...'")
            
            return results
            
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}", exc_info=True)
            return []
        