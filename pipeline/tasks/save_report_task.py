#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from logger import get_logger

logger = get_logger(__name__)

def save_report(input_file_path: str, output_file_path: str):
    """
    임시 마크다운 파일을 최종 목적지에 저장
    
    Args:
        input_file_path (str): 임시 저장된 마크다운 파일 경로
        output_file_path (str): 최종 저장할 마크다운 파일 경로
        
    Returns:
        str: 최종 저장된 파일 경로
    """
    logger.info(f"🔄 마크다운 리포트 최종 저장 시작: {output_file_path}")
    
    try:
        # 출력 디렉토리가 없으면 생성
        output_dir = os.path.dirname(output_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 파일 복사
        shutil.copy2(input_file_path, output_file_path)
        
        logger.info(f"✅ 마크다운 리포트 저장 완료: {output_file_path}")
        return output_file_path
        
    except Exception as e:
        logger.error(f"❌ 마크다운 리포트 저장 실패: {str(e)}")
        raise 