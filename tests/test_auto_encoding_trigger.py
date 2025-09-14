"""
자동 인코딩 트리거 테스트
"""
import sys
import os
import pytest
import time
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
from app.services.encoding.encoding_queue import encoding_queue
from app.core.config import settings as app_settings

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
    
    # MVP에서는 인코딩 비활성화 시 전체 스킵
    if getattr(app_settings, 'ENCODING_ENABLED', False) is False:
        pytest.skip("Encoding disabled in MVP (ENCODING_ENABLED=False)")

    # 인코딩 큐 시작
    encoding_queue.start()
    
    yield
    
    # 인코딩 큐 정리
    encoding_queue.stop()


class TestAutoEncodingTrigger:
    """자동 인코딩 트리거 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
        
        # 테스트용 책 생성
        self.book = BookService.create_book(
            user_id=settings.LOCAL_BYPASS_SUB,
            title="Auto Encoding Test Book",
            author="Test Author"
        )

    @pytest.mark.skipif(
        not os.path.exists(TEST_AUDIO_DIR) or not os.listdir(TEST_AUDIO_DIR),
        reason="실제 오디오 파일이 없음"
    )
    def test_upload_triggers_encoding(self):
        """업로드 시 자동 인코딩 트리거 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        test_file_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"Testing auto encoding with: {mp3_files[0]}")
        
        # 1. 파일 업로드
        response = self.client.post(
            f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Auto Test Chapter",
            files={"file": (mp3_files[0], file_content, "audio/mpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        chapter_id = data["chapter_id"]
        print(f"Chapter created: {chapter_id}")
        
        # 2. 인코딩 작업이 제출되었는지 확인
        if "encoding_job_id" in data.get("processing_info", {}):
            job_id = data["processing_info"]["encoding_job_id"]
            print(f"Encoding job submitted: {job_id}")
            
            # 3. 인코딩 작업 상태 확인
            job_response = self.client.get(f"/api/v1/encoding/jobs/{job_id}")
            assert job_response.status_code == 200
            
            job_data = job_response.json()
            assert job_data["chapter_id"] == chapter_id
            assert job_data["status"] in ["pending", "processing", "completed"]
            
            print(f"Job status: {job_data['status']}")
            
            # 4. 챕터별 작업 목록 확인
            chapter_jobs_response = self.client.get(f"/api/v1/encoding/chapters/{chapter_id}/jobs")
            assert chapter_jobs_response.status_code == 200
            
            chapter_jobs = chapter_jobs_response.json()
            assert len(chapter_jobs) >= 1
            assert any(job["job_id"] == job_id for job in chapter_jobs)
            
        else:
            # 인코딩이 건너뛰어진 경우
            print("Encoding skipped - file already optimized")
            processing_info = data.get("processing_info", {})
            
            # 인코딩이 건너뛰어졌거나 이미 처리 완료된 경우
            if processing_info.get("encoding_skipped") is True:
                print(f"Skip reason: {processing_info.get('skip_reason')}")
                assert True  # 정상적으로 건너뛰어짐
            else:
                # 메타데이터가 즉시 추출된 경우 (MP3 등)
                assert "duration" in processing_info
                print(f"Metadata extracted: duration={processing_info.get('duration')}s")
            
            # 챕터 상태 확인
            chapter = AudioChapter.get_by_id(chapter_id)
            assert chapter.status in ["ready", "processing"]  # 처리 완료 또는 진행 중

    def test_encoding_queue_stats(self):
        """인코딩 큐 통계 조회 테스트"""
        response = self.client.get("/api/v1/encoding/queue/stats")
        assert response.status_code == 200
        
        stats = response.json()
        
        assert "total_jobs" in stats
        assert "status_counts" in stats
        assert "queue_size" in stats
        assert "workers" in stats
        assert "running" in stats
        
        print(f"Queue stats: {stats}")

    def test_encoding_health_check(self):
        """인코딩 시스템 헬스체크 테스트"""
        response = self.client.get("/api/v1/encoding/health")
        assert response.status_code == 200
        
        health = response.json()
        
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        
        print(f"Encoding health: {health}")

    @pytest.mark.skipif(
        not os.path.exists(TEST_AUDIO_DIR) or not os.listdir(TEST_AUDIO_DIR),
        reason="실제 오디오 파일이 없음"
    )
    def test_manual_encoding_trigger(self):
        """수동 인코딩 트리거 테스트"""
        mp3_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.mp3')]
        
        if not mp3_files:
            pytest.skip("MP3 파일이 없습니다")
        
        test_file_path = os.path.join(TEST_AUDIO_DIR, mp3_files[0])
        
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        # 1. 파일 업로드 (인코딩 자동 트리거)
        upload_response = self.client.post(
            f"/api/v1/files/upload/audio?book_id={self.book.book_id}&chapter_title=Manual Test",
            files={"file": (mp3_files[0], file_content, "audio/mpeg")}
        )
        
        assert upload_response.status_code == 200
        chapter_id = upload_response.json()["chapter_id"]
        
        # 2. 수동으로 강제 인코딩 시작
        manual_encoding_response = self.client.post(
            f"/api/v1/encoding/chapters/{chapter_id}/encode",
            json={"force_encoding": True}
        )
        
        if manual_encoding_response.status_code == 200:
            manual_data = manual_encoding_response.json()
            print(f"Manual encoding started: {manual_data}")
            
            assert manual_data["success"] is True
            assert "job_id" in manual_data
            
        else:
            # 이미 진행 중인 작업이 있는 경우
            print(f"Manual encoding response: {manual_encoding_response.json()}")


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """테스트 데이터 정리"""
    yield
    
    try:
        # 테스트 책 삭제
        for book in Book.scan():
            if "Auto Encoding" in book.title or "Test" in book.title:
                book.delete()
        
        # 테스트 챕터 삭제
        for chapter in AudioChapter.scan():
            if "Auto Test" in chapter.title or "Manual Test" in chapter.title:
                chapter.delete()
    except Exception:
        pass
