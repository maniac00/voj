"""
인코딩 파일 관리 테스트
"""
import sys
import os
import pytest
import tempfile
import shutil
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from app.services.encoding.file_manager import EncodingFileManager, file_manager
from app.core.config import settings as app_settings
from app.services.books import BookService
from app.models.book import Book


@pytest.fixture(autouse=True)
def _local_setup():
    """로컬 환경 설정"""
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    
    # 테이블 생성
    if not Book.exists():
        Book.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    
    # MVP에서는 인코딩 비활성화 시 전체 스킵 (파일 관리/환경 API도 비활성)
    if getattr(app_settings, 'ENCODING_ENABLED', False) is False:
        pytest.skip("Encoding disabled in MVP (ENCODING_ENABLED=False)")

    yield


class TestEncodingFileManager:
    """인코딩 파일 관리자 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = EncodingFileManager()
        
        # 임시 스토리지 경로 설정
        self.file_manager.base_storage_path = self.temp_dir
    
    def teardown_method(self):
        """각 테스트 후 정리"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_file_paths(self):
        """파일 경로 생성 테스트"""
        paths = self.file_manager.get_file_paths(
            book_id="test-book",
            chapter_id="test-chapter", 
            filename="test audio.mp3"
        )
        
        assert "uploads_dir" in paths
        assert "media_dir" in paths
        assert "temp_dir" in paths
        assert "original_file" in paths
        assert "encoded_file" in paths
        
        # 파일명 정리 확인
        assert "test_audio.mp3" in paths["original_file"]
        assert "test_audio.m4a" in paths["encoded_file"]
    
    def test_ensure_directories(self):
        """디렉토리 생성 테스트"""
        book_id = "test-book"
        
        self.file_manager.ensure_directories(book_id)
        
        paths = self.file_manager.get_file_paths(book_id, "dummy", "dummy.mp3")
        
        assert os.path.exists(paths["uploads_dir"])
        assert os.path.exists(paths["media_dir"])
        assert os.path.exists(paths["temp_dir"])
    
    def test_sanitize_filename(self):
        """파일명 정리 테스트"""
        test_cases = [
            ("normal file.mp3", "normal_file.mp3"),
            ("file<>:\"/\\|?*.mp3", "file_________.mp3"),
            ("  multiple   spaces  .mp3", "multiple_spaces.mp3"),
            ("___underscores___.mp3", "underscores.mp3"),
            ("", "unnamed_audio"),
        ]
        
        for input_name, expected in test_cases:
            result = self.file_manager._sanitize_filename(input_name)
            assert result == expected, f"Input: {input_name}, Expected: {expected}, Got: {result}"
    
    def test_file_info_existing_file(self):
        """존재하는 파일 정보 조회 테스트"""
        # 테스트 파일 생성
        test_file_path = os.path.join(self.temp_dir, "test.mp3")
        test_content = b"test audio content"
        
        with open(test_file_path, 'wb') as f:
            f.write(test_content)
        
        file_info = self.file_manager.get_file_info(test_file_path)
        
        assert file_info.exists
        assert file_info.size == len(test_content)
        assert file_info.path == test_file_path
        assert file_info.created_at is not None
    
    def test_file_info_nonexistent_file(self):
        """존재하지 않는 파일 정보 조회 테스트"""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.mp3")
        
        file_info = self.file_manager.get_file_info(nonexistent_path)
        
        assert not file_info.exists
        assert file_info.size == 0
        assert file_info.path == nonexistent_path
    
    def test_get_encoding_file_set(self):
        """인코딩 파일 세트 조회 테스트"""
        book_id = "test-book"
        chapter_id = "test-chapter"
        filename = "test.mp3"
        
        # 디렉토리 생성
        self.file_manager.ensure_directories(book_id)
        paths = self.file_manager.get_file_paths(book_id, chapter_id, filename)
        
        # 원본 파일 생성
        with open(paths["original_file"], 'wb') as f:
            f.write(b"original content")
        
        # 인코딩 파일 생성
        with open(paths["encoded_file"], 'wb') as f:
            f.write(b"encoded content")
        
        # 파일 세트 조회
        file_set = self.file_manager.get_encoding_file_set(book_id, chapter_id, filename)
        
        assert file_set.original_file is not None
        assert file_set.original_file.exists
        assert file_set.encoded_file is not None
        assert file_set.encoded_file.exists
        assert file_set.total_size > 0
    
    def test_validate_file_integrity(self):
        """파일 무결성 검증 테스트"""
        # 정상 파일
        test_file_path = os.path.join(self.temp_dir, "valid.mp3")
        with open(test_file_path, 'wb') as f:
            f.write(b"valid content")
        
        is_valid, error = self.file_manager.validate_file_integrity(test_file_path)
        assert is_valid
        assert error is None
        
        # 빈 파일
        empty_file_path = os.path.join(self.temp_dir, "empty.mp3")
        with open(empty_file_path, 'wb') as f:
            pass  # 빈 파일
        
        is_valid, error = self.file_manager.validate_file_integrity(empty_file_path)
        assert not is_valid
        assert "Empty file" in error
        
        # 존재하지 않는 파일
        is_valid, error = self.file_manager.validate_file_integrity("/nonexistent/file.mp3")
        assert not is_valid
        assert "not found" in error.lower()
    
    def test_cleanup_temp_files(self):
        """임시 파일 정리 테스트"""
        book_id = "test-book"
        chapter_id = "test-chapter"
        
        # 디렉토리 생성
        self.file_manager.ensure_directories(book_id)
        paths = self.file_manager.get_file_paths(book_id, chapter_id, "test.mp3")
        
        # 임시 파일 생성
        temp_files = [
            f"temp_{chapter_id}_file1.mp3",
            f"temp_{chapter_id}_file2.m4a",
            f"temp_other_chapter_file.mp3"  # 다른 챕터
        ]
        
        for temp_file in temp_files:
            temp_path = os.path.join(paths["temp_dir"], temp_file)
            with open(temp_path, 'wb') as f:
                f.write(b"temp content")
        
        # 특정 챕터 임시 파일 정리
        removed_count = self.file_manager.cleanup_temp_files(book_id, chapter_id)
        
        assert removed_count == 2  # 해당 챕터 파일 2개만 삭제
        
        # 다른 챕터 파일은 남아있어야 함
        remaining_files = os.listdir(paths["temp_dir"])
        assert len(remaining_files) == 1
        assert "other_chapter" in remaining_files[0]
    
    def test_storage_stats(self):
        """스토리지 통계 테스트"""
        book_id = "test-book"
        
        # 디렉토리 및 파일 생성
        self.file_manager.ensure_directories(book_id)
        paths = self.file_manager.get_file_paths(book_id, "ch1", "test.mp3")
        
        # 원본 파일
        with open(paths["original_file"], 'wb') as f:
            f.write(b"original content" * 100)  # 1600 bytes
        
        # 인코딩 파일
        with open(paths["encoded_file"], 'wb') as f:
            f.write(b"encoded content" * 50)   # 800 bytes
        
        stats = self.file_manager.get_storage_stats()
        
        assert stats["total_books"] == 1
        assert stats["total_original_files"] == 1
        assert stats["total_encoded_files"] == 1
        assert stats["original_size"] == 1600
        assert stats["encoded_size"] == 800
        assert stats["compression_ratio"] == 2.0  # 1600/800


class TestStorageAPI:
    """스토리지 관리 API 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
        
        # 테스트용 책 생성
        self.book = BookService.create_book(
            user_id=settings.LOCAL_BYPASS_SUB,
            title="Storage Test Book",
            author="Test Author"
        )
    
    def test_get_storage_stats_api(self):
        """스토리지 통계 API 테스트"""
        response = self.client.get("/api/v1/encoding/storage/stats")
        assert response.status_code == 200
        
        data = response.json()
        
        assert "disk_usage" in data
        assert "file_stats" in data
        assert "timestamp" in data
        
        print(f"Storage stats: {data}")
    
    def test_cleanup_storage_api(self):
        """스토리지 정리 API 테스트"""
        response = self.client.post("/api/v1/encoding/storage/cleanup?max_age_hours=1")
        assert response.status_code == 200
        
        data = response.json()
        
        assert data["success"] is True
        assert "temp_files_removed" in data
        assert "old_jobs_removed" in data
        
        print(f"Cleanup result: {data}")
    
    def test_optimize_book_storage_api(self):
        """책 스토리지 최적화 API 테스트"""
        response = self.client.post(f"/api/v1/encoding/storage/optimize/{self.book.book_id}")
        assert response.status_code == 200
        
        data = response.json()
        
        assert data["success"] is True
        assert data["book_id"] == self.book.book_id
        assert "optimization_results" in data
        
        print(f"Optimization result: {data}")


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """테스트 데이터 정리"""
    yield
    
    try:
        # 테스트 책 삭제
        for book in Book.scan():
            if "Storage Test" in book.title or "Test" in book.title:
                book.delete()
    except Exception:
        pass
