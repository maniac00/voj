"""
인코딩 큐 시스템 테스트
"""
import sys
import os
import pytest
import tempfile
import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.encoding.encoding_queue import (
    EncodingQueue,
    EncodingJob,
    EncodingStatus,
    EncodingStatusManager
)
from app.services.encoding.ffmpeg_service import EncodingResult


class TestEncodingQueue:
    """인코딩 큐 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.queue = EncodingQueue(max_workers=1)  # 테스트용으로 워커 1개만
    
    def teardown_method(self):
        """각 테스트 후 정리"""
        self.queue.stop()
    
    def test_queue_initialization(self):
        """큐 초기화 테스트"""
        assert self.queue.max_workers == 1
        assert not self.queue.running
        assert len(self.queue.jobs) == 0
        assert len(self.queue.workers) == 0
    
    def test_queue_start_stop(self):
        """큐 시작/중지 테스트"""
        # 시작
        self.queue.start()
        assert self.queue.running
        assert len(self.queue.workers) == 1
        
        # 중지
        self.queue.stop()
        assert not self.queue.running
        assert len(self.queue.workers) == 0
    
    def test_submit_job(self):
        """작업 제출 테스트"""
        job_id = self.queue.submit_job(
            chapter_id="test-chapter",
            book_id="test-book",
            input_path="/test/input.mp3",
            output_path="/test/output.m4a"
        )
        
        assert job_id
        assert job_id in self.queue.jobs
        
        job = self.queue.get_job(job_id)
        assert job is not None
        assert job.chapter_id == "test-chapter"
        assert job.status == EncodingStatus.PENDING
    
    def test_job_status_queries(self):
        """작업 상태 조회 테스트"""
        # 여러 작업 제출
        job_id1 = self.queue.submit_job("ch1", "book1", "/test1.mp3", "/out1.m4a")
        job_id2 = self.queue.submit_job("ch2", "book1", "/test2.mp3", "/out2.m4a")
        
        # 전체 조회
        assert len(self.queue.jobs) == 2
        
        # 상태별 조회
        pending_jobs = self.queue.get_jobs_by_status(EncodingStatus.PENDING)
        assert len(pending_jobs) == 2
        
        # 챕터별 조회
        ch1_jobs = self.queue.get_jobs_by_chapter("ch1")
        assert len(ch1_jobs) == 1
        assert ch1_jobs[0].job_id == job_id1
    
    def test_job_cancellation(self):
        """작업 취소 테스트"""
        job_id = self.queue.submit_job("test-ch", "test-book", "/test.mp3", "/out.m4a")
        
        # 취소 성공
        success = self.queue.cancel_job(job_id)
        assert success
        
        job = self.queue.get_job(job_id)
        assert job.status == EncodingStatus.CANCELLED
        
        # 이미 취소된 작업 재취소 시도
        success = self.queue.cancel_job(job_id)
        assert not success
    
    @patch('os.path.exists')
    @patch('app.services.encoding.encoding_queue.FFmpegEncodingService')
    def test_job_processing_success(self, mock_ffmpeg_service, mock_exists):
        """작업 처리 성공 테스트"""
        # 파일 존재 모킹
        mock_exists.return_value = True
        
        # FFmpeg 서비스 모킹
        mock_service = MagicMock()
        mock_service.encode_audio.return_value = EncodingResult(
            success=True,
            output_path="/test/output.m4a",
            metadata={"duration": 120, "bitrate": 56, "channels": 1},
            original_size=1000000,
            encoded_size=300000,
            processing_time=5.0
        )
        mock_ffmpeg_service.return_value = mock_service
        
        # AudioChapter 업데이트 모킹
        with patch('app.services.encoding.encoding_queue.AudioChapter') as mock_chapter_class:
            mock_chapter = MagicMock()
            mock_chapter_class.get_by_id.return_value = mock_chapter
            
            # 큐 시작 및 작업 제출
            self.queue.start()
            job_id = self.queue.submit_job("test-ch", "test-book", "/test.mp3", "/out.m4a")
            
            # 작업 완료까지 대기
            time.sleep(0.5)
            
            job = self.queue.get_job(job_id)
            assert job.status == EncodingStatus.COMPLETED
            assert job.progress == 1.0
            assert job.metadata is not None
            
            # AudioChapter 업데이트 확인
            mock_chapter.mark_processing_completed.assert_called_once()
    
    @patch('os.path.exists')
    @patch('app.services.encoding.encoding_queue.FFmpegEncodingService')
    def test_job_processing_failure(self, mock_ffmpeg_service, mock_exists):
        """작업 처리 실패 테스트"""
        # 파일 존재 모킹
        mock_exists.return_value = True
        
        # FFmpeg 서비스 실패 모킹
        mock_service = MagicMock()
        mock_service.encode_audio.return_value = EncodingResult(
            success=False,
            error="FFmpeg encoding failed"
        )
        mock_ffmpeg_service.return_value = mock_service
        
        # AudioChapter 업데이트 모킹
        with patch('app.services.encoding.encoding_queue.AudioChapter') as mock_chapter_class:
            mock_chapter = MagicMock()
            mock_chapter_class.get_by_id.return_value = mock_chapter
            
            # 큐 시작 및 작업 제출
            self.queue.start()
            job_id = self.queue.submit_job("test-ch", "test-book", "/test.mp3", "/out.m4a")
            
            # 작업 완료까지 대기
            time.sleep(0.5)
            
            job = self.queue.get_job(job_id)
            assert job.status == EncodingStatus.FAILED
            assert job.error_message == "FFmpeg encoding failed"
            
            # AudioChapter 에러 상태 업데이트 확인
            mock_chapter.mark_processing_error.assert_called_once()
    
    def test_job_retry(self):
        """작업 재시도 테스트"""
        job_id = self.queue.submit_job("test-ch", "test-book", "/test.mp3", "/out.m4a")
        
        # 강제로 실패 상태로 변경
        job = self.queue.get_job(job_id)
        job.status = EncodingStatus.FAILED
        job.error_message = "Test failure"
        
        # 재시도
        success = self.queue.retry_job(job_id)
        assert success
        
        job = self.queue.get_job(job_id)
        assert job.status == EncodingStatus.PENDING
        assert job.retry_count == 1
        assert job.error_message is None
    
    def test_queue_stats(self):
        """큐 통계 테스트"""
        # 여러 상태의 작업 생성
        job_id1 = self.queue.submit_job("ch1", "book1", "/test1.mp3", "/out1.m4a")
        job_id2 = self.queue.submit_job("ch2", "book1", "/test2.mp3", "/out2.m4a")
        
        # 하나는 실패 상태로 변경
        job2 = self.queue.get_job(job_id2)
        job2.status = EncodingStatus.FAILED
        
        stats = self.queue.get_queue_stats()
        
        assert stats["total_jobs"] == 2
        assert stats["status_counts"]["pending"] == 1
        assert stats["status_counts"]["failed"] == 1
        assert stats["queue_size"] >= 0
        assert stats["workers"] == 0  # 시작하지 않았으므로


class TestEncodingStatusManager:
    """인코딩 상태 관리자 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.status_manager = EncodingStatusManager()
        self.received_notifications = []
    
    def test_subscribe_unsubscribe(self):
        """구독/구독해제 테스트"""
        def callback(status_data):
            self.received_notifications.append(status_data)
        
        # 구독
        subscription_id = self.status_manager.subscribe("test-chapter", callback)
        assert subscription_id
        assert "test-chapter" in self.status_manager.subscribers
        
        # 구독해제
        self.status_manager.unsubscribe("test-chapter", callback)
        assert "test-chapter" not in self.status_manager.subscribers
    
    def test_status_notification(self):
        """상태 알림 테스트"""
        def callback(status_data):
            self.received_notifications.append(status_data)
        
        self.status_manager.subscribe("test-chapter", callback)
        
        # 가짜 작업으로 알림 전송
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter",
            book_id="test-book",
            input_path="/test.mp3",
            output_path="/out.m4a",
            status=EncodingStatus.PROCESSING,
            created_at=datetime.now(timezone.utc),
            progress=0.5
        )
        
        self.status_manager.notify_status_change(job)
        
        assert len(self.received_notifications) == 1
        notification = self.received_notifications[0]
        assert notification["chapter_id"] == "test-chapter"
        assert notification["status"] == "processing"
        assert notification["progress"] == 0.5


class TestEncodingIntegration:
    """인코딩 시스템 통합 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.queue = EncodingQueue(max_workers=1)
        self.status_manager = EncodingStatusManager()
        self.queue.add_status_callback(self.status_manager.notify_status_change)
    
    def teardown_method(self):
        """각 테스트 후 정리"""
        self.queue.stop()
    
    def test_end_to_end_workflow(self):
        """전체 워크플로우 테스트"""
        notifications = []
        
        def status_callback(status_data):
            notifications.append(status_data)
        
        # 상태 변경 구독
        self.status_manager.subscribe("test-chapter", status_callback)
        
        # 작업 제출
        job_id = self.queue.submit_job(
            chapter_id="test-chapter",
            book_id="test-book", 
            input_path="/test/input.mp3",
            output_path="/test/output.m4a"
        )
        
        # 초기 상태 확인
        job = self.queue.get_job(job_id)
        assert job.status == EncodingStatus.PENDING
        
        # 통계 확인
        stats = self.queue.get_queue_stats()
        assert stats["total_jobs"] == 1
        assert stats["status_counts"]["pending"] == 1
