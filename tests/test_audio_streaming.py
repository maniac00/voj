"""
오디오 스트리밍 URL 생성 및 재생 테스트
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from app.services.books import BookService
from app.models.book import Book
from app.models.audio_chapter import AudioChapter

# 테스트 오디오 파일 경로
TEST_AUDIO_DIR = "/Users/kimsungwook/dev/voj/tmp_test_media/sample_audiobooks"


@pytest.fixture(autouse=True)
def _local_setup():
    """로컬 환경 설정"""
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    
    # 테이블 생성
    if not Book.exists():
        Book.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    if not AudioChapter.exists():
        AudioChapter.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    
    yield


class TestAudioStreaming:
    """오디오 스트리밍 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
        
        # 테스트용 책 생성
        self.book = BookService.create_book(
            user_id=settings.LOCAL_BYPASS_SUB,
            title="Streaming Test Book",
            author="Test Author"
        )

    @pytest.mark.skipif(
        not os.path.exists(TEST_AUDIO_DIR) or not os.listdir(TEST_AUDIO_DIR),
        reason="실제 오디오 파일이 없음"
    )
    def test_upload_and_stream_real_audio(self):
        """실제 오디오 파일 업로드 및 스트리밍 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        test_file_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"Testing streaming with: {mp3_files[0]}")
        
        # 1. 파일 업로드
        upload_response = self.client.post(
            f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Streaming Test",
            files={"file": (mp3_files[0], file_content, "audio/mpeg")}
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        chapter_id = upload_data["chapter_id"]
        
        print(f"Chapter created: {chapter_id}")
        
        # 2. 스트리밍 URL 생성
        stream_response = self.client.get(
            f"/api/v1/audio/{self.book.book_id}/chapters/{chapter_id}/stream"
        )
        
        assert stream_response.status_code == 200
        stream_data = stream_response.json()
        
        assert "streaming_url" in stream_data
        assert "expires_at" in stream_data
        assert "duration" in stream_data
        
        streaming_url = stream_data["streaming_url"]
        print(f"Streaming URL: {streaming_url}")
        print(f"Duration: {stream_data['duration']}초")
        
        # 3. 스트리밍 URL로 파일 접근 테스트
        # URL에서 파일 경로 추출하여 직접 테스트
        if "/files/" in streaming_url:
            file_key = streaming_url.split("/files/")[-1]
            
            file_response = self.client.get(f"/api/v1/files/{file_key}")
            
            if file_response.status_code == 200:
                print("✅ 스트리밍 URL로 파일 접근 성공")
                
                # Content-Type 확인
                content_type = file_response.headers.get("content-type", "")
                assert content_type.startswith("audio/"), f"Expected audio content type, got: {content_type}"
                
                # 파일 크기 확인
                content_length = file_response.headers.get("content-length")
                if content_length:
                    print(f"Content-Length: {content_length} bytes")
                
            else:
                print(f"❌ 스트리밍 URL 접근 실패: {file_response.status_code}")
                print(f"Response: {file_response.text}")

    def test_streaming_url_generation_without_file(self):
        """파일 없이 스트리밍 URL 생성 테스트 (실패 케이스)"""
        # 존재하지 않는 챕터로 스트리밍 URL 요청
        response = self.client.get(
            f"/api/v1/audio/{self.book.book_id}/chapters/nonexistent-chapter/stream"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_streaming_url_unauthorized(self):
        """권한 없는 스트리밍 URL 요청 테스트"""
        # 다른 사용자의 책으로 요청
        other_book = BookService.create_book(
            user_id="other-user",
            title="Other User Book",
            author="Other Author"
        )
        
        response = self.client.get(
            f"/api/v1/audio/{other_book.book_id}/chapters/any-chapter/stream"
        )
        
        assert response.status_code == 404  # 소유권 확인으로 404 반환

    def test_streaming_url_format(self):
        """스트리밍 URL 형식 테스트"""
        # 임시 챕터 생성 (파일 없이)
        from app.models.audio_chapter import FileInfo
        
        chapter = AudioChapter(
            chapter_id="test-streaming-chapter",
            book_id=self.book.book_id,
            chapter_number=1,
            title="Test Streaming Chapter",
            status="ready",
            file_info=FileInfo(
                original_name="test.mp3",
                file_size=1000000,
                mime_type="audio/mpeg",
                local_path="/fake/path/test.mp3"  # 가짜 경로
            )
        )
        chapter.save()
        
        # 스트리밍 URL 요청 (파일이 없어서 실패할 것)
        response = self.client.get(
            f"/api/v1/audio/{self.book.book_id}/chapters/{chapter.chapter_id}/stream"
        )
        
        # 파일이 없어서 404가 나와야 함
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """테스트 데이터 정리"""
    yield
    
    try:
        # 테스트 책 삭제
        for book in Book.scan():
            if "Streaming Test" in book.title or "Other User" in book.title:
                book.delete()
        
        # 테스트 챕터 삭제
        for chapter in AudioChapter.scan():
            if "Streaming Test" in chapter.title or "test-streaming" in chapter.chapter_id:
                chapter.delete()
    except Exception:
        pass
