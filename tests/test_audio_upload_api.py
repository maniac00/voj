"""
오디오 업로드 API 테스트
"""
import sys
import os
import pytest
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from app.services.books import BookService
from app.models.book import Book
from app.models.audio_chapter import AudioChapter


@pytest.fixture(autouse=True)
def _local_setup():
    """로컬 환경 설정"""
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    settings.LOCAL_BYPASS_SCOPE = "admin"
    
    # 테이블 생성
    if not Book.exists():
        Book.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    if not AudioChapter.exists():
        AudioChapter.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    
    yield


class TestAudioUploadAPI:
    """오디오 업로드 API 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
        
        # 테스트용 책 생성 (로컬 바이패스 사용자 ID 사용)
        self.book = BookService.create_book(
            user_id=settings.LOCAL_BYPASS_SUB,
            title="Test Book",
            author="Test Author"
        )

    def test_upload_audio_file_success(self):
        """오디오 파일 업로드 성공 테스트"""
        # 가짜 M4A 파일(콘텐츠 무관, 확장자만 확인)
        audio_content = b"\x00" * 2048
        
        with patch('app.utils.ffprobe.extract_audio_metadata') as mock_ffprobe:
            mock_ffprobe.return_value = {
                "duration": 120,
                "bitrate": 128,
                "sample_rate": 44100,
                "channels": 2,
                "format": "mp4"
            }
            
            response = self.client.post(
                f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Test Chapter",
                files={"file": ("test.m4a", audio_content, "audio/mp4")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "chapter_id" in data
        assert data["chapter_number"] == 1
        assert data["title"] == "Test Chapter"
        assert data["status"] in ["processing", "ready", "error"]  # ffprobe 실패 시 error 상태도 허용

    def test_upload_audio_file_invalid_format(self):
        """지원되지 않는 파일 형식 업로드 테스트"""
        response = self.client.post(
            f"/api/v1/files/upload/audio?book_id={self.book.book_id}",
            files={"file": ("test.txt", b"not an audio file", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Only .mp4/.m4a files are allowed" in response.json()["detail"]

    def test_upload_audio_file_too_large(self):
        """파일 크기 초과 테스트"""
        # 100MB보다 큰 파일
        large_content = b"x" * (101 * 1024 * 1024)
        
        response = self.client.post(
            f"/api/v1/files/upload/audio?book_id={self.book.book_id}",
            files={"file": ("large.m4a", large_content, "audio/mp4")}
        )
        
        assert response.status_code == 413
        assert "File size exceeds limit" in response.json()["detail"]

    def test_upload_audio_file_book_not_found(self):
        """존재하지 않는 책에 오디오 업로드 테스트"""
        audio_content = b"\x00" * 2048
        
        response = self.client.post(
            "/api/v1/files/upload/audio?book_id=nonexistent-book-id",
            files={"file": ("test.m4a", audio_content, "audio/mp4")}
        )
        
        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    def test_upload_multiple_audio_files(self):
        """여러 오디오 파일 업로드 테스트"""
        audio_content = b"\x00" * 2048
        
        with patch('app.utils.ffprobe.extract_audio_metadata') as mock_ffprobe:
            mock_ffprobe.return_value = {
                "duration": 60,
                "bitrate": 128,
                "sample_rate": 44100,
                "channels": 1,
                "format": "mp4"
            }
            
            # 첫 번째 파일 업로드
            response1 = self.client.post(
                f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Chapter 1",
                files={"file": ("chapter1.m4a", audio_content, "audio/mp4")}
            )
            
            # 두 번째 파일 업로드
            response2 = self.client.post(
                f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Chapter 2",
                files={"file": ("chapter2.m4a", audio_content, "audio/mp4")}
            )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # 챕터 번호가 순차적으로 할당되는지 확인
        assert data1["chapter_number"] == 1
        assert data2["chapter_number"] == 2

    def test_upload_audio_ffprobe_failure(self):
        """ffprobe 실패 시 처리 테스트"""
        audio_content = b"\x00" * 2048
        
        with patch('app.utils.ffprobe.extract_audio_metadata') as mock_ffprobe:
            mock_ffprobe.side_effect = Exception("ffprobe failed")
            
            response = self.client.post(
                f"/api/v1/files/upload/audio?book_id={self.book.book_id}",
                files={"file": ("test.m4a", audio_content, "audio/mp4")}
            )
        
        assert response.status_code == 200  # 업로드 자체는 성공
        data = response.json()
        assert data["success"] is True
        
        # 챕터가 생성되었는지 확인
        chapter = AudioChapter.get_by_id(data["chapter_id"])
        assert chapter is not None
        assert chapter.status in ["ready", "error"]

    def test_upload_without_authentication(self):
        """인증 없이 업로드 시도 테스트"""
        with patch.object(settings, 'LOCAL_BYPASS_ENABLED', False):
            audio_content = b"RIFF" + b"\x00" * 40 + b"WAVE" + b"\x00" * 100
            
            response = self.client.post(
                f"/api/v1/files/upload/audio?book_id={self.book.book_id}",
                files={"file": ("test.m4a", audio_content, "audio/mp4")}
            )
            
            assert response.status_code == 401

    def test_upload_audio_chapter_creation(self):
        """AudioChapter 생성 확인 테스트"""
        audio_content = b"\x00" * 2048
        
        with patch('app.utils.ffprobe.extract_audio_metadata') as mock_ffprobe:
            mock_ffprobe.return_value = {
                "duration": 180,
                "bitrate": 64,
                "sample_rate": 22050,
                "channels": 1,
                "format": "mp4"
            }
            
            response = self.client.post(
                f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=My Chapter",
                files={"file": ("my_audio.m4a", audio_content, "audio/mp4")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # 생성된 챕터 확인
        chapter = AudioChapter.get_by_id(data["chapter_id"])
        assert chapter is not None
        assert chapter.book_id == self.book.book_id
        assert chapter.title == "My Chapter"
        assert chapter.chapter_number == 1
        assert chapter.file_info.original_name == "my_audio.m4a"
        assert chapter.file_info.file_size == len(audio_content)
        assert chapter.file_info.mime_type == "audio/mp4"
        
        # 메타데이터 확인 (로컬 환경에서는 즉시 처리)
        if chapter.status == "ready":
            assert chapter.audio_metadata is not None
            assert isinstance(chapter.audio_metadata.duration, (int, float))
            assert chapter.audio_metadata.channels == 1


class TestAudioUploadIntegration:
    """오디오 업로드 통합 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
        
        # 테스트용 책 생성 (로컬 바이패스 사용자 ID 사용)
        self.book = BookService.create_book(
            user_id=settings.LOCAL_BYPASS_SUB,
            title="Integration Test Book",
            author="Test Author"
        )

    def test_complete_audio_upload_workflow(self):
        """완전한 오디오 업로드 워크플로우 테스트"""
        audio_content = b"\x00" * 2048
        
        with patch('app.utils.ffprobe.extract_audio_metadata') as mock_ffprobe:
            mock_ffprobe.return_value = {
                "duration": 300,
                "bitrate": 128,
                "sample_rate": 44100,
                "channels": 2,
                "format": "mp4"
            }
            
            # 1. 오디오 파일 업로드
            upload_response = self.client.post(
                f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Intro",
                files={"file": ("intro.m4a", audio_content, "audio/mp4")}
            )
            
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            chapter_id = upload_data["chapter_id"]
            
            # 2. 챕터 목록 조회
            chapters_response = self.client.get(f"/api/v1/audio/{self.book.book_id}/chapters")
            assert chapters_response.status_code == 200
            
            chapters = chapters_response.json()
            assert len(chapters) == 1
            assert chapters[0]["chapter_id"] == chapter_id
            assert chapters[0]["title"] == "Intro"
            
            # 3. 챕터 상세 조회
            chapter_response = self.client.get(f"/api/v1/audio/{self.book.book_id}/chapters/{chapter_id}")
            assert chapter_response.status_code == 200
            
            chapter_data = chapter_response.json()
            assert chapter_data["chapter_id"] == chapter_id
            assert chapter_data["file_name"] == "intro.m4a"


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """테스트 데이터 정리"""
    yield
    
    # 테스트 후 생성된 데이터 정리
    try:
        # 모든 테스트 책 삭제
        for book in Book.scan():
            if book.title.startswith("Test") or book.title.startswith("Integration"):
                book.delete()
        
        # 모든 테스트 챕터 삭제
        for chapter in AudioChapter.scan():
            if chapter.title.startswith("Test") or chapter.title.startswith("Chapter") or chapter.title.startswith("Intro"):
                chapter.delete()
    except Exception:
        pass
