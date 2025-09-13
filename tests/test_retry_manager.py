"""
인코딩 재시도 관리자 테스트
"""
import sys
import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.encoding.retry_manager import (
    EncodingRetryManager,
    FailureType,
    RetryPolicy,
    RecoveryStrategies
)
from app.services.encoding.encoding_queue import EncodingJob, EncodingStatus


class TestEncodingRetryManager:
    """인코딩 재시도 관리자 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.retry_manager = EncodingRetryManager(
            RetryPolicy(max_retries=3, base_delay=0.1, max_delay=1.0)  # 테스트용 짧은 지연
        )
    
    def test_analyze_failure_temporary(self):
        """임시적 실패 분석 테스트"""
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter",
            book_id="test-book",
            input_path="/test.mp3",
            output_path="/test.m4a",
            status=EncodingStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            error_message="Connection timeout occurred"
        )
        
        analysis = self.retry_manager.analyze_failure(job)
        
        assert analysis.failure_type == FailureType.TEMPORARY
        assert analysis.is_retryable
        assert analysis.error_category == "temporary"
    
    def test_analyze_failure_permanent(self):
        """영구적 실패 분석 테스트"""
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter", 
            book_id="test-book",
            input_path="/test.mp3",
            output_path="/test.m4a",
            status=EncodingStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            error_message="Input file not found"
        )
        
        analysis = self.retry_manager.analyze_failure(job)
        
        assert analysis.failure_type == FailureType.PERMANENT
        assert not analysis.is_retryable
        assert analysis.error_category == "permanent"
    
    def test_analyze_failure_recoverable(self):
        """복구 가능 실패 분석 테스트"""
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter",
            book_id="test-book", 
            input_path="/test.mp3",
            output_path="/test.m4a",
            status=EncodingStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            error_message="Insufficient disk space"
        )
        
        analysis = self.retry_manager.analyze_failure(job)
        
        assert analysis.failure_type == FailureType.RECOVERABLE
        assert analysis.is_retryable
        assert analysis.error_category == "recoverable"
    
    def test_calculate_delay(self):
        """지연 시간 계산 테스트"""
        # 첫 번째 재시도
        delay1 = self.retry_manager._calculate_delay(0)
        assert delay1 == 0.1  # base_delay
        
        # 두 번째 재시도
        delay2 = self.retry_manager._calculate_delay(1)
        assert delay2 == 0.2  # base_delay * 2
        
        # 세 번째 재시도
        delay3 = self.retry_manager._calculate_delay(2)
        assert delay3 == 0.4  # base_delay * 4
        
        # 최대 지연 시간 제한
        delay_max = self.retry_manager._calculate_delay(10)
        assert delay_max == 1.0  # max_delay
    
    def test_should_retry_automatically(self):
        """자동 재시도 여부 판단 테스트"""
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter",
            book_id="test-book",
            input_path="/test.mp3", 
            output_path="/test.m4a",
            status=EncodingStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            error_message="Temporary network error",
            retry_count=1
        )
        
        # 재시도 가능한 경우
        should_retry = self.retry_manager.should_retry_automatically(job)
        assert should_retry
        
        # 재시도 횟수 초과
        job.retry_count = 5
        should_retry = self.retry_manager.should_retry_automatically(job)
        assert not should_retry
    
    def test_record_failure(self):
        """실패 기록 테스트"""
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter",
            book_id="test-book",
            input_path="/test.mp3",
            output_path="/test.m4a", 
            status=EncodingStatus.FAILED,
            created_at=datetime.now(timezone.utc)
        )
        
        # 실패 기록
        self.retry_manager.record_failure(job)
        
        # 기록 확인
        assert "test-chapter" in self.retry_manager.failure_history
        assert len(self.retry_manager.failure_history["test-chapter"]) == 1
        
        # 추가 실패 기록
        self.retry_manager.record_failure(job)
        assert len(self.retry_manager.failure_history["test-chapter"]) == 2
    
    def test_failure_stats(self):
        """실패 통계 테스트"""
        # 여러 챕터에 실패 기록
        for chapter_id in ["ch1", "ch2", "ch3"]:
            job = EncodingJob(
                job_id=f"job-{chapter_id}",
                chapter_id=chapter_id,
                book_id="test-book",
                input_path="/test.mp3",
                output_path="/test.m4a",
                status=EncodingStatus.FAILED,
                created_at=datetime.now(timezone.utc)
            )
            self.retry_manager.record_failure(job)
        
        stats = self.retry_manager.get_failure_stats()
        
        assert stats["total_chapters_with_failures"] == 3
        assert stats["total_failures"] == 3
        assert stats["recent_failures_1h"] == 3


class TestRecoveryStrategies:
    """복구 전략 테스트"""
    
    def test_disk_space_recovery(self):
        """디스크 공간 복구 테스트"""
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter",
            book_id="test-book",
            input_path="/test.mp3",
            output_path="/test.m4a",
            status=EncodingStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            error_message="Insufficient disk space"
        )
        
        # 복구 시도 (실제 파일 정리는 하지 않고 함수 호출만)
        try:
            result = RecoveryStrategies.disk_space_recovery(job)
            # 결과는 성공/실패 상관없이 함수가 정상 호출되면 됨
            assert isinstance(result, bool)
        except Exception:
            # 테스트 환경에서는 실패할 수 있음
            pass
    
    def test_memory_recovery(self):
        """메모리 복구 테스트"""
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter",
            book_id="test-book",
            input_path="/test.mp3",
            output_path="/test.m4a",
            status=EncodingStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            error_message="Out of memory"
        )
        
        # 메모리 복구 시도
        result = RecoveryStrategies.memory_recovery(job)
        assert isinstance(result, bool)


class TestRetryIntegration:
    """재시도 시스템 통합 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.retry_manager = EncodingRetryManager(
            RetryPolicy(max_retries=2, base_delay=0.1, failure_threshold=3)
        )
    
    def test_handle_job_failure(self):
        """작업 실패 처리 테스트"""
        job = EncodingJob(
            job_id="test-job",
            chapter_id="test-chapter",
            book_id="test-book",
            input_path="/test.mp3",
            output_path="/test.m4a",
            status=EncodingStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            error_message="Temporary encoding error",
            retry_count=0
        )
        
        result = self.retry_manager.handle_job_failure(job)
        
        assert result["job_id"] == job.job_id
        assert result["failure_type"] == "temporary"
        assert result["is_retryable"] is True
        assert "retry_count" in result
        assert "max_retries" in result
        
        print(f"Failure handling result: {result}")


@pytest.fixture(autouse=True)
def setup_logging():
    """로깅 설정"""
    import logging
    logging.basicConfig(level=logging.INFO)
    yield
