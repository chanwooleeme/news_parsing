# common/logger.py

import logging

def get_logger(name: str = "news_project") -> logging.Logger:
    """
    공통 Logger 생성기.
    Airflow, FastAPI, Scripts 어디서든 일관된 포맷 사용 가능.
    """

    logger = logging.getLogger(name)
    
    if logger.handlers:
        # 이미 핸들러가 있으면 중복 추가 방지
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    return logger
