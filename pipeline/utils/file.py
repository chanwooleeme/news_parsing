from typing import List, Dict, Any
import json
import os


def ensure_directory_exists(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def read_json_file(file_path: str) -> List[str]:
    with open(file_path, 'r') as file:
        return json.load(file)

def write_json_file(data: List[str], file_path: str) -> None:
    with open(file_path, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def list_directories(path: str) -> list:
    """폴더 안의 모든 디렉토리 이름 리턴"""
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

def list_files(path: str, extension: str = None) -> list:
    """폴더 안의 모든 파일 이름 리턴 (확장자 필터 가능)"""
    files = os.listdir(path)
    if extension:
        return [f for f in files if f.endswith(extension)]
    return files

def join_path(*paths: str) -> str:
    """경로 합치기"""
    return os.path.join(*paths)

def splitext_filename(filename: str) -> str:
    """확장자 제거한 파일명만 추출"""
    return os.path.splitext(filename)[0]

def read_text_file(filepath: str, encoding: str = "utf-8") -> str:
    with open(filepath, 'rb') as file:
        content = file.read()
    # 에러 무시하고 디코딩 ('replace'는 잘못된 문자를 ''로 대체)
    return content.decode(encoding, errors='replace')

def save_dict_as_json(data: dict, save_dir: str, filename: str) -> None:
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, filename + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def make_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)
