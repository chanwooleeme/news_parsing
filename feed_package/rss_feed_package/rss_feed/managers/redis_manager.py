import redis
import hashlib


class RedisManager:
    """Redis 서버와 상호작용을 관리하는 클래스"""
    
    def __init__(self, host='redis', port=6379, db=0, password=None):
        """
        RedisManager 초기화
        
        Args:
            host (str): Redis 서버 호스트
            port (int): Redis 서버 포트
            db (int): Redis 데이터베이스 번호
            password (str, optional): Redis 서버 비밀번호
        """
        self.redis_client = redis.Redis(host=host, port=port, db=db, password=password)
        
    def is_new_url(self, url, rss_url=None):
        """
        URL이 이전에 처리된 적이 있는지 확인
        
        Args:
            url (str): 확인할 URL
            rss_url (str, optional): RSS 피드 URL
            
        Returns:
            bool: 새로운 URL이면 True, 이미 처리된 URL이면 False
        """
        url_hash = self._create_hash(url)
        key = f"{rss_url}:{url_hash}" if rss_url else url_hash
        
        if self.redis_client.exists(key):
            return False
        
        # Redis에 URL 해시 저장 (1시간 유효)
        self.redis_client.set(key, 1, ex=3600)
        return True
    
    def _create_hash(self, url):
        """
        URL의 해시값 생성
        
        Args:
            url (str): 해시할 URL
            
        Returns:
            str: URL의 MD5 해시값
        """
        return hashlib.md5(url.encode()).hexdigest() 