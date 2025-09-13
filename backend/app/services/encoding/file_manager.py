"""
인코딩 파일 관리 서비스
원본 파일과 인코딩 결과 파일의 생명주기 관리
"""
from __future__ import annotations

import os
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import settings


@dataclass
class FileInfo:
    """파일 정보"""
    path: str
    size: int
    created_at: datetime
    exists: bool


@dataclass
class EncodingFileSet:
    """인코딩 관련 파일 세트"""
    original_file: Optional[FileInfo]
    encoded_file: Optional[FileInfo]
    temp_files: List[FileInfo]
    total_size: int


class EncodingFileManager:
    """인코딩 파일 관리자"""
    
    def __init__(self):
        self.base_storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
        self.uploads_dir = "uploads"
        self.media_dir = "media"
        self.temp_dir = "temp"
    
    def get_file_paths(self, book_id: str, chapter_id: str, filename: str) -> Dict[str, str]:
        """파일 경로들 생성"""
        safe_filename = self._sanitize_filename(filename)
        base_name = Path(safe_filename).stem
        
        paths = {
            'uploads_dir': os.path.join(self.base_storage_path, "book", book_id, self.uploads_dir),
            'media_dir': os.path.join(self.base_storage_path, "book", book_id, self.media_dir),
            'temp_dir': os.path.join(self.base_storage_path, "book", book_id, self.temp_dir),
            'original_file': os.path.join(self.base_storage_path, "book", book_id, self.uploads_dir, safe_filename),
            'encoded_file': os.path.join(self.base_storage_path, "book", book_id, self.media_dir, f"{base_name}.m4a"),
            'temp_original': os.path.join(self.base_storage_path, "book", book_id, self.temp_dir, f"temp_{chapter_id}_{safe_filename}"),
            'temp_encoded': os.path.join(self.base_storage_path, "book", book_id, self.temp_dir, f"temp_{chapter_id}_{base_name}.m4a")
        }
        
        return paths
    
    def ensure_directories(self, book_id: str) -> None:
        """필요한 디렉토리 생성"""
        paths = self.get_file_paths(book_id, "dummy", "dummy.mp3")
        
        for dir_key in ['uploads_dir', 'media_dir', 'temp_dir']:
            dir_path = paths[dir_key]
            os.makedirs(dir_path, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """파일명 정리"""
        import re
        
        # 안전하지 않은 문자 제거
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 연속된 공백과 언더스코어 정리
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # 앞뒤 점과 언더스코어 제거
        sanitized = sanitized.strip('._')
        
        return sanitized or "unnamed_audio"
    
    def get_file_info(self, file_path: str) -> FileInfo:
        """파일 정보 조회"""
        exists = os.path.exists(file_path)
        size = os.path.getsize(file_path) if exists else 0
        
        if exists:
            stat = os.stat(file_path)
            created_at = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
        else:
            created_at = datetime.now(timezone.utc)
        
        return FileInfo(
            path=file_path,
            size=size,
            created_at=created_at,
            exists=exists
        )
    
    def get_encoding_file_set(self, book_id: str, chapter_id: str, filename: str) -> EncodingFileSet:
        """인코딩 관련 파일 세트 조회"""
        paths = self.get_file_paths(book_id, chapter_id, filename)
        
        original_file = self.get_file_info(paths['original_file'])
        encoded_file = self.get_file_info(paths['encoded_file'])
        
        # 임시 파일들 찾기
        temp_files = []
        temp_dir = paths['temp_dir']
        
        if os.path.exists(temp_dir):
            for temp_filename in os.listdir(temp_dir):
                if chapter_id in temp_filename:
                    temp_path = os.path.join(temp_dir, temp_filename)
                    temp_files.append(self.get_file_info(temp_path))
        
        total_size = (
            (original_file.size if original_file.exists else 0) +
            (encoded_file.size if encoded_file.exists else 0) +
            sum(tf.size for tf in temp_files if tf.exists)
        )
        
        return EncodingFileSet(
            original_file=original_file if original_file.exists else None,
            encoded_file=encoded_file if encoded_file.exists else None,
            temp_files=temp_files,
            total_size=total_size
        )
    
    def move_temp_to_final(self, temp_path: str, final_path: str) -> bool:
        """임시 파일을 최종 위치로 이동"""
        try:
            # 최종 디렉토리 생성
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            # 파일 이동
            shutil.move(temp_path, final_path)
            
            return True
            
        except Exception as e:
            print(f"Failed to move file {temp_path} → {final_path}: {e}")
            return False
    
    def copy_to_temp(self, source_path: str, temp_path: str) -> bool:
        """파일을 임시 위치로 복사"""
        try:
            # 임시 디렉토리 생성
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            # 파일 복사
            shutil.copy2(source_path, temp_path)
            
            return True
            
        except Exception as e:
            print(f"Failed to copy file {source_path} → {temp_path}: {e}")
            return False
    
    def cleanup_temp_files(self, book_id: str, chapter_id: str) -> int:
        """특정 챕터의 임시 파일 정리"""
        paths = self.get_file_paths(book_id, chapter_id, "dummy.mp3")
        temp_dir = paths['temp_dir']
        
        if not os.path.exists(temp_dir):
            return 0
        
        removed_count = 0
        
        try:
            for filename in os.listdir(temp_dir):
                if chapter_id in filename:
                    temp_file_path = os.path.join(temp_dir, filename)
                    try:
                        os.remove(temp_file_path)
                        removed_count += 1
                    except Exception as e:
                        print(f"Failed to remove temp file {temp_file_path}: {e}")
        
        except Exception as e:
            print(f"Failed to list temp directory {temp_dir}: {e}")
        
        return removed_count
    
    def cleanup_old_temp_files(self, max_age_hours: int = 24) -> int:
        """오래된 임시 파일 정리"""
        if not os.path.exists(self.base_storage_path):
            return 0
        
        removed_count = 0
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        
        try:
            # 모든 책의 temp 디렉토리 탐색
            for book_dir in os.listdir(os.path.join(self.base_storage_path, "book")):
                temp_dir = os.path.join(self.base_storage_path, "book", book_dir, self.temp_dir)
                
                if os.path.exists(temp_dir):
                    for filename in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, filename)
                        
                        try:
                            if os.path.getmtime(file_path) < cutoff_time:
                                os.remove(file_path)
                                removed_count += 1
                        except Exception as e:
                            print(f"Failed to remove old temp file {file_path}: {e}")
        
        except Exception as e:
            print(f"Failed to cleanup old temp files: {e}")
        
        return removed_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """스토리지 사용량 통계"""
        stats = {
            'total_books': 0,
            'total_original_files': 0,
            'total_encoded_files': 0,
            'total_temp_files': 0,
            'original_size': 0,
            'encoded_size': 0,
            'temp_size': 0,
            'compression_ratio': 0.0
        }
        
        if not os.path.exists(os.path.join(self.base_storage_path, "book")):
            return stats
        
        try:
            book_dirs = os.listdir(os.path.join(self.base_storage_path, "book"))
            stats['total_books'] = len(book_dirs)
            
            for book_id in book_dirs:
                book_path = os.path.join(self.base_storage_path, "book", book_id)
                
                # uploads 디렉토리
                uploads_path = os.path.join(book_path, self.uploads_dir)
                if os.path.exists(uploads_path):
                    for filename in os.listdir(uploads_path):
                        file_path = os.path.join(uploads_path, filename)
                        if os.path.isfile(file_path):
                            stats['total_original_files'] += 1
                            stats['original_size'] += os.path.getsize(file_path)
                
                # media 디렉토리
                media_path = os.path.join(book_path, self.media_dir)
                if os.path.exists(media_path):
                    for filename in os.listdir(media_path):
                        file_path = os.path.join(media_path, filename)
                        if os.path.isfile(file_path):
                            stats['total_encoded_files'] += 1
                            stats['encoded_size'] += os.path.getsize(file_path)
                
                # temp 디렉토리
                temp_path = os.path.join(book_path, self.temp_dir)
                if os.path.exists(temp_path):
                    for filename in os.listdir(temp_path):
                        file_path = os.path.join(temp_path, filename)
                        if os.path.isfile(file_path):
                            stats['total_temp_files'] += 1
                            stats['temp_size'] += os.path.getsize(file_path)
            
            # 압축률 계산
            if stats['original_size'] > 0 and stats['encoded_size'] > 0:
                stats['compression_ratio'] = stats['original_size'] / stats['encoded_size']
        
        except Exception as e:
            print(f"Failed to get storage stats: {e}")
        
        return stats
    
    def delete_chapter_files(self, book_id: str, chapter_id: str, filename: str, 
                           keep_original: bool = False) -> Dict[str, bool]:
        """챕터 관련 파일 삭제"""
        paths = self.get_file_paths(book_id, chapter_id, filename)
        results = {}
        
        # 인코딩 파일 삭제
        if os.path.exists(paths['encoded_file']):
            try:
                os.remove(paths['encoded_file'])
                results['encoded_file'] = True
            except Exception as e:
                print(f"Failed to delete encoded file: {e}")
                results['encoded_file'] = False
        
        # 원본 파일 삭제 (옵션)
        if not keep_original and os.path.exists(paths['original_file']):
            try:
                os.remove(paths['original_file'])
                results['original_file'] = True
            except Exception as e:
                print(f"Failed to delete original file: {e}")
                results['original_file'] = False
        
        # 임시 파일 정리
        temp_removed = self.cleanup_temp_files(book_id, chapter_id)
        results['temp_files_removed'] = temp_removed
        
        return results
    
    def archive_original_file(self, book_id: str, chapter_id: str, filename: str) -> bool:
        """원본 파일을 아카이브 디렉토리로 이동"""
        try:
            paths = self.get_file_paths(book_id, chapter_id, filename)
            archive_dir = os.path.join(self.base_storage_path, "book", book_id, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            
            archive_path = os.path.join(archive_dir, filename)
            
            if os.path.exists(paths['original_file']):
                shutil.move(paths['original_file'], archive_path)
                return True
            
        except Exception as e:
            print(f"Failed to archive original file: {e}")
        
        return False
    
    def restore_from_archive(self, book_id: str, chapter_id: str, filename: str) -> bool:
        """아카이브에서 원본 파일 복원"""
        try:
            paths = self.get_file_paths(book_id, chapter_id, filename)
            archive_path = os.path.join(self.base_storage_path, "book", book_id, "archive", filename)
            
            if os.path.exists(archive_path):
                os.makedirs(paths['uploads_dir'], exist_ok=True)
                shutil.move(archive_path, paths['original_file'])
                return True
            
        except Exception as e:
            print(f"Failed to restore from archive: {e}")
        
        return False
    
    def validate_file_integrity(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """파일 무결성 검증"""
        if not os.path.exists(file_path):
            return False, "File not found"
        
        try:
            # 파일 크기 확인
            size = os.path.getsize(file_path)
            if size == 0:
                return False, "Empty file"
            
            # 파일 읽기 가능 확인
            with open(file_path, 'rb') as f:
                f.read(1024)  # 첫 1KB 읽기 시도
            
            return True, None
            
        except Exception as e:
            return False, f"File integrity check failed: {str(e)}"
    
    def get_disk_usage(self, book_id: Optional[str] = None) -> Dict[str, int]:
        """디스크 사용량 조회"""
        if book_id:
            # 특정 책의 사용량
            book_path = os.path.join(self.base_storage_path, "book", book_id)
            if not os.path.exists(book_path):
                return {'total': 0, 'uploads': 0, 'media': 0, 'temp': 0, 'archive': 0}
            
            usage = {}
            for subdir in ['uploads', 'media', 'temp', 'archive']:
                dir_path = os.path.join(book_path, subdir)
                usage[subdir] = self._get_directory_size(dir_path)
            
            usage['total'] = sum(usage.values())
            return usage
        
        else:
            # 전체 사용량
            total_usage = {'total': 0, 'uploads': 0, 'media': 0, 'temp': 0, 'archive': 0}
            
            books_path = os.path.join(self.base_storage_path, "book")
            if os.path.exists(books_path):
                for book_id in os.listdir(books_path):
                    book_usage = self.get_disk_usage(book_id)
                    for key in total_usage:
                        total_usage[key] += book_usage.get(key, 0)
            
            return total_usage
    
    def _get_directory_size(self, dir_path: str) -> int:
        """디렉토리 크기 계산"""
        if not os.path.exists(dir_path):
            return 0
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(dir_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        pass
        except Exception:
            pass
        
        return total_size
    
    def optimize_storage(self, book_id: str) -> Dict[str, Any]:
        """스토리지 최적화 (중복 파일 제거, 압축 등)"""
        results = {
            'original_files_archived': 0,
            'temp_files_removed': 0,
            'space_saved': 0,
            'errors': []
        }
        
        try:
            book_path = os.path.join(self.base_storage_path, "book", book_id)
            
            # 1. 인코딩 완료된 파일의 원본을 아카이브로 이동
            uploads_path = os.path.join(book_path, self.uploads_dir)
            media_path = os.path.join(book_path, self.media_dir)
            
            if os.path.exists(uploads_path) and os.path.exists(media_path):
                for upload_file in os.listdir(uploads_path):
                    upload_path = os.path.join(uploads_path, upload_file)
                    base_name = Path(upload_file).stem
                    
                    # 해당하는 인코딩 파일이 있는지 확인
                    encoded_file = os.path.join(media_path, f"{base_name}.m4a")
                    
                    if os.path.exists(encoded_file):
                        # 원본 파일 아카이브
                        if self.archive_original_file(book_id, "dummy", upload_file):
                            results['original_files_archived'] += 1
                            results['space_saved'] += os.path.getsize(upload_path)
            
            # 2. 오래된 임시 파일 정리
            temp_removed = self.cleanup_old_temp_files(max_age_hours=1)  # 1시간 이상된 임시 파일
            results['temp_files_removed'] = temp_removed
            
        except Exception as e:
            results['errors'].append(str(e))
        
        return results


# 전역 파일 관리자 인스턴스
file_manager = EncodingFileManager()


def get_chapter_file_info(book_id: str, chapter_id: str, filename: str) -> EncodingFileSet:
    """챕터 파일 정보 조회 (편의 함수)"""
    return file_manager.get_encoding_file_set(book_id, chapter_id, filename)


def cleanup_chapter_files(book_id: str, chapter_id: str, filename: str, keep_original: bool = False) -> Dict[str, bool]:
    """챕터 파일 정리 (편의 함수)"""
    return file_manager.delete_chapter_files(book_id, chapter_id, filename, keep_original)


def get_storage_usage() -> Dict[str, int]:
    """전체 스토리지 사용량 (편의 함수)"""
    return file_manager.get_disk_usage()
