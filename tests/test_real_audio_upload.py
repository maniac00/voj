"""
실제 오디오 파일을 사용한 업로드 테스트
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


class TestRealAudioUpload:
    """실제 오디오 파일 업로드 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
        
        # 테스트용 책 생성
        self.book = BookService.create_book(
            user_id=settings.LOCAL_BYPASS_SUB,
            title="나의 아버지 순교자 주기철 목사",
            author="주영수",
            genre="종교",
            language="ko"
        )

    @pytest.mark.skipif(
        not os.path.exists(TEST_AUDIO_DIR) or not os.listdir(TEST_AUDIO_DIR),
        reason="실제 오디오 파일이 없음"
    )
    def test_upload_real_mp3_file(self):
        """실제 MP3 파일 업로드 테스트"""
        # 첫 번째 MP3 파일 찾기
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        test_file_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        
        # 파일 읽기
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"Testing with file: {mp3_files[0]}")
        print(f"File size: {len(file_content) / (1024*1024):.2f} MB")
        
        # 업로드 요청
        response = self.client.post(
            f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Chapter 1",
            files={"file": (mp3_files[0], file_content, "audio/mpeg")}
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response body: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "chapter_id" in data
        assert data["chapter_number"] >= 1  # 파일명에서 추출한 번호 사용
        assert data["title"] == "Chapter 1"
        
        # 생성된 챕터 확인
        chapter = AudioChapter.get_by_id(data["chapter_id"])
        assert chapter is not None
        assert chapter.book_id == self.book.book_id
        assert chapter.file_info.original_name == mp3_files[0]
        
        print(f"Chapter status: {chapter.status}")
        if chapter.status == "ready" and chapter.audio_metadata:
            print(f"Duration: {chapter.audio_metadata.duration}초")
            print(f"Bitrate: {chapter.audio_metadata.bitrate}kbps")
            print(f"Sample rate: {chapter.audio_metadata.sample_rate}Hz")
            print(f"Channels: {chapter.audio_metadata.channels}")

    @pytest.mark.skipif(
        not os.path.exists(TEST_AUDIO_DIR) or not os.listdir(TEST_AUDIO_DIR),
        reason="실제 오디오 파일이 없음"
    )
    def test_upload_multiple_real_files(self):
        """여러 실제 MP3 파일 업로드 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')][:2]  # 처음 2개만
        
        if len(mp3_files) < 2:
            pytest.skip("MP3 파일이 2개 미만입니다")
        
        uploaded_chapters = []
        
        for i, filename in enumerate(mp3_files):
            file_path = os.path.join(TEST_AUDIO_DIR, filename)
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            print(f"Uploading: {filename}")
            
            response = self.client.post(
                f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Chapter {i+1}",
                files={"file": (filename, file_content, "audio/mpeg")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["chapter_number"] >= 1  # 파일명에서 추출한 번호 사용
            
            uploaded_chapters.append(data)
        
        # 챕터 목록 조회로 확인
        chapters_response = self.client.get(f"/api/v1/audio/{self.book.book_id}/chapters")
        assert chapters_response.status_code == 200
        
        chapters = chapters_response.json()
        assert len(chapters) == len(mp3_files)
        
        # 챕터 번호 순서 확인
        for i, chapter in enumerate(sorted(chapters, key=lambda x: x["chapter_number"])):
            assert chapter["chapter_number"] == i + 1

    def test_mp3_metadata_extraction(self):
        """MP3 메타데이터 추출 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        test_file_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        
        # ffprobe 직접 테스트
        from app.utils.ffprobe import extract_audio_metadata
        
        try:
            metadata = extract_audio_metadata(test_file_path)
            
            print(f"Extracted metadata: {metadata}")
            
            assert metadata["duration"] > 0
            assert metadata["format"] in ["mp3", "mpeg"]
            assert metadata["sample_rate"] in [44100, 48000, 22050]
            assert metadata["channels"] in [1, 2]
            
            if metadata["bitrate"]:
                assert metadata["bitrate"] > 0
                
        except Exception as e:
            pytest.fail(f"Metadata extraction failed: {e}")


@pytest.fixture(autouse=True) 
def cleanup_test_data():
    """테스트 데이터 정리"""
    yield
    
    try:
        # 테스트 책 삭제
        for book in Book.scan():
            if "순교자" in book.title or "Test" in book.title:
                book.delete()
        
        # 테스트 챕터 삭제  
        for chapter in AudioChapter.scan():
            if "Chapter" in chapter.title:
                chapter.delete()
    except Exception:
        pass
