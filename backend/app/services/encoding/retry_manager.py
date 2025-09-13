"""
인코딩 재시도 관리 서비스
실패한 인코딩 작업의 자동 재시도 및 복구 로직
"""
from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import logging

from app.services.encoding.encoding_queue import EncodingJob, EncodingStatus, encoding_queue


class FailureType(Enum):
    """실패 유형"""
    TEMPORARY = "temporary"      # 임시적 실패 (재시도 가능)
    PERMANENT = "permanent"      # 영구적 실패 (재시도 불가)
    RECOVERABLE = "recoverable"  # 복구 가능 (조건부 재시도)


@dataclass
class RetryPolicy:
    """재시도 정책"""
    max_retries: int = 3
    base_delay: float = 1.0  # 초
    max_delay: float = 60.0  # 초
    backoff_multiplier: float = 2.0
    failure_threshold: int = 5  # 연속 실패 임계값


@dataclass
class FailureAnalysis:
    """실패 분석 결과"""
    failure_type: FailureType
    is_retryable: bool
    suggested_delay: float
    recovery_action: Optional[str] = None
    error_category: str = "unknown"


class EncodingRetryManager:
    """인코딩 재시도 관리자"""
    
    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.failure_history: Dict[str, List[datetime]] = {}
        self.recovery_callbacks: List[Callable[[EncodingJob], None]] = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # 자동 재시도 스케줄러
        self.scheduler_thread: Optional[threading.Thread] = None
        self.scheduler_running = False
    
    def analyze_failure(self, job: EncodingJob) -> FailureAnalysis:
        """실패 원인 분석"""
        error_message = (job.error_message or "").lower()
        
        # 임시적 실패 패턴
        temporary_patterns = [
            "timeout",
            "network",
            "connection",
            "temporary",
            "busy",
            "locked"
        ]
        
        # 영구적 실패 패턴
        permanent_patterns = [
            "not found",
            "permission denied",
            "invalid format",
            "corrupted",
            "unsupported",
            "codec not found"
        ]
        
        # 복구 가능 실패 패턴
        recoverable_patterns = [
            "disk space",
            "memory",
            "resource",
            "quota"
        ]
        
        # 패턴 매칭
        for pattern in permanent_patterns:
            if pattern in error_message:
                return FailureAnalysis(
                    failure_type=FailureType.PERMANENT,
                    is_retryable=False,
                    suggested_delay=0,
                    error_category="permanent",
                    recovery_action="Check input file and format"
                )
        
        for pattern in recoverable_patterns:
            if pattern in error_message:
                return FailureAnalysis(
                    failure_type=FailureType.RECOVERABLE,
                    is_retryable=True,
                    suggested_delay=self._calculate_delay(job.retry_count) * 2,  # 더 긴 지연
                    error_category="recoverable",
                    recovery_action="Check system resources and try again"
                )
        
        for pattern in temporary_patterns:
            if pattern in error_message:
                return FailureAnalysis(
                    failure_type=FailureType.TEMPORARY,
                    is_retryable=True,
                    suggested_delay=self._calculate_delay(job.retry_count),
                    error_category="temporary",
                    recovery_action="Automatic retry will be attempted"
                )
        
        # 기본값 (알 수 없는 오류는 임시적으로 간주)
        return FailureAnalysis(
            failure_type=FailureType.TEMPORARY,
            is_retryable=job.retry_count < self.retry_policy.max_retries,
            suggested_delay=self._calculate_delay(job.retry_count),
            error_category="unknown"
        )
    
    def _calculate_delay(self, retry_count: int) -> float:
        """재시도 지연 시간 계산 (지수 백오프)"""
        delay = self.retry_policy.base_delay * (
            self.retry_policy.backoff_multiplier ** retry_count
        )
        return min(delay, self.retry_policy.max_delay)
    
    def should_retry_automatically(self, job: EncodingJob) -> bool:
        """자동 재시도 여부 판단"""
        # 재시도 횟수 확인
        if job.retry_count >= self.retry_policy.max_retries:
            return False
        
        # 실패 분석
        analysis = self.analyze_failure(job)
        if not analysis.is_retryable:
            return False
        
        # 연속 실패 횟수 확인
        with self.lock:
            failures = self.failure_history.get(job.chapter_id, [])
            recent_failures = [
                f for f in failures 
                if (datetime.now(timezone.utc) - f).total_seconds() < 3600  # 1시간 내
            ]
            
            if len(recent_failures) >= self.retry_policy.failure_threshold:
                self.logger.warning(
                    f"Too many recent failures for chapter {job.chapter_id}: "
                    f"{len(recent_failures)} in last hour"
                )
                return False
        
        return True
    
    def record_failure(self, job: EncodingJob) -> None:
        """실패 기록"""
        with self.lock:
            if job.chapter_id not in self.failure_history:
                self.failure_history[job.chapter_id] = []
            
            self.failure_history[job.chapter_id].append(datetime.now(timezone.utc))
            
            # 오래된 기록 정리 (24시간 이상)
            cutoff_time = datetime.now(timezone.utc).timestamp() - (24 * 3600)
            self.failure_history[job.chapter_id] = [
                f for f in self.failure_history[job.chapter_id]
                if f.timestamp() > cutoff_time
            ]
    
    def schedule_retry(self, job: EncodingJob) -> bool:
        """재시도 스케줄링"""
        if not self.should_retry_automatically(job):
            return False
        
        analysis = self.analyze_failure(job)
        delay = analysis.suggested_delay
        
        # 재시도 스케줄링
        def retry_job():
            time.sleep(delay)
            success = encoding_queue.retry_job(job.job_id)
            
            if success:
                self.logger.info(
                    f"Automatic retry scheduled for job {job.job_id} "
                    f"after {delay:.1f}s delay (attempt {job.retry_count + 1})"
                )
            else:
                self.logger.warning(f"Failed to schedule retry for job {job.job_id}")
        
        # 백그라운드에서 재시도 실행
        retry_thread = threading.Thread(target=retry_job, daemon=True)
        retry_thread.start()
        
        return True
    
    def handle_job_failure(self, job: EncodingJob) -> Dict[str, any]:
        """작업 실패 처리"""
        # 실패 기록
        self.record_failure(job)
        
        # 실패 분석
        analysis = self.analyze_failure(job)
        
        # 복구 콜백 실행
        for callback in self.recovery_callbacks:
            try:
                callback(job)
            except Exception as e:
                self.logger.error(f"Recovery callback error: {e}")
        
        # 자동 재시도 스케줄링
        retry_scheduled = False
        if analysis.is_retryable:
            retry_scheduled = self.schedule_retry(job)
        
        result = {
            "job_id": job.job_id,
            "chapter_id": job.chapter_id,
            "failure_type": analysis.failure_type.value,
            "error_category": analysis.error_category,
            "is_retryable": analysis.is_retryable,
            "retry_scheduled": retry_scheduled,
            "suggested_delay": analysis.suggested_delay,
            "recovery_action": analysis.recovery_action,
            "retry_count": job.retry_count,
            "max_retries": self.retry_policy.max_retries
        }
        
        self.logger.error(
            f"Encoding job {job.job_id} failed: {job.error_message} "
            f"(type: {analysis.failure_type.value}, retryable: {analysis.is_retryable})"
        )
        
        return result
    
    def add_recovery_callback(self, callback: Callable[[EncodingJob], None]) -> None:
        """복구 콜백 추가"""
        self.recovery_callbacks.append(callback)
    
    def get_failure_stats(self) -> Dict[str, any]:
        """실패 통계 조회"""
        with self.lock:
            total_chapters = len(self.failure_history)
            total_failures = sum(len(failures) for failures in self.failure_history.values())
            
            # 최근 1시간 내 실패
            recent_cutoff = datetime.now(timezone.utc).timestamp() - 3600
            recent_failures = 0
            
            for failures in self.failure_history.values():
                recent_failures += len([
                    f for f in failures if f.timestamp() > recent_cutoff
                ])
            
            return {
                "total_chapters_with_failures": total_chapters,
                "total_failures": total_failures,
                "recent_failures_1h": recent_failures,
                "failure_threshold": self.retry_policy.failure_threshold,
                "max_retries": self.retry_policy.max_retries
            }
    
    def clear_failure_history(self, chapter_id: Optional[str] = None) -> int:
        """실패 기록 정리"""
        with self.lock:
            if chapter_id:
                # 특정 챕터 기록 정리
                removed = len(self.failure_history.get(chapter_id, []))
                if chapter_id in self.failure_history:
                    del self.failure_history[chapter_id]
                return removed
            else:
                # 전체 기록 정리
                total_removed = sum(len(failures) for failures in self.failure_history.values())
                self.failure_history.clear()
                return total_removed
    
    def start_scheduler(self) -> None:
        """재시도 스케줄러 시작"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        def scheduler_loop():
            while self.scheduler_running:
                try:
                    # 실패한 작업들 확인
                    failed_jobs = encoding_queue.get_jobs_by_status(EncodingStatus.FAILED)
                    
                    for job in failed_jobs:
                        if self.should_retry_automatically(job):
                            analysis = self.analyze_failure(job)
                            
                            # 지연 시간이 지났는지 확인
                            if job.completed_at:
                                elapsed = (datetime.now(timezone.utc) - job.completed_at).total_seconds()
                                if elapsed >= analysis.suggested_delay:
                                    success = encoding_queue.retry_job(job.job_id)
                                    if success:
                                        self.logger.info(f"Auto-retried job {job.job_id}")
                    
                    # 30초마다 확인
                    time.sleep(30)
                    
                except Exception as e:
                    self.logger.error(f"Retry scheduler error: {e}")
                    time.sleep(60)  # 에러 시 1분 대기
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Encoding retry scheduler started")
    
    def stop_scheduler(self) -> None:
        """재시도 스케줄러 중지"""
        self.scheduler_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Encoding retry scheduler stopped")


# 전역 재시도 관리자
retry_manager = EncodingRetryManager()


def handle_encoding_failure(job: EncodingJob) -> Dict[str, any]:
    """인코딩 실패 처리 (편의 함수)"""
    return retry_manager.handle_job_failure(job)


def get_retry_stats() -> Dict[str, any]:
    """재시도 통계 조회 (편의 함수)"""
    return retry_manager.get_failure_stats()


def clear_failure_history(chapter_id: Optional[str] = None) -> int:
    """실패 기록 정리 (편의 함수)"""
    return retry_manager.clear_failure_history(chapter_id)


# 인코딩 큐에 실패 처리 콜백 등록
def setup_retry_system() -> None:
    """재시도 시스템 설정"""
    def on_job_failure(job: EncodingJob) -> None:
        if job.status == EncodingStatus.FAILED:
            retry_manager.handle_job_failure(job)
    
    encoding_queue.add_status_callback(on_job_failure)
    retry_manager.start_scheduler()


def cleanup_retry_system() -> None:
    """재시도 시스템 정리"""
    retry_manager.stop_scheduler()


# 특정 오류 유형별 복구 전략
class RecoveryStrategies:
    """복구 전략 모음"""
    
    @staticmethod
    def disk_space_recovery(job: EncodingJob) -> bool:
        """디스크 공간 부족 복구"""
        try:
            from app.services.encoding.file_manager import file_manager
            
            # 임시 파일 정리
            removed = file_manager.cleanup_old_temp_files(max_age_hours=1)
            
            if removed > 0:
                logging.info(f"Freed space by removing {removed} temp files for job {job.job_id}")
                return True
                
        except Exception as e:
            logging.error(f"Disk space recovery failed: {e}")
        
        return False
    
    @staticmethod
    def memory_recovery(job: EncodingJob) -> bool:
        """메모리 부족 복구"""
        try:
            # 다른 인코딩 작업 일시 중지 (메모리 확보)
            import gc
            gc.collect()
            
            logging.info(f"Memory recovery attempted for job {job.job_id}")
            return True
            
        except Exception as e:
            logging.error(f"Memory recovery failed: {e}")
        
        return False
    
    @staticmethod
    def file_corruption_recovery(job: EncodingJob) -> bool:
        """파일 손상 복구"""
        try:
            from app.services.encoding.file_manager import file_manager
            
            # 파일 무결성 재확인
            is_valid, error = file_manager.validate_file_integrity(job.input_path)
            
            if not is_valid:
                logging.error(f"Input file validation failed for job {job.job_id}: {error}")
                return False
            
            logging.info(f"File integrity verified for job {job.job_id}")
            return True
            
        except Exception as e:
            logging.error(f"File corruption recovery failed: {e}")
        
        return False


# 복구 전략 등록
def register_recovery_strategies() -> None:
    """복구 전략 등록"""
    def recovery_callback(job: EncodingJob) -> None:
        if not job.error_message:
            return
        
        error_msg = job.error_message.lower()
        
        # 디스크 공간 문제
        if "disk" in error_msg or "space" in error_msg:
            RecoveryStrategies.disk_space_recovery(job)
        
        # 메모리 문제
        elif "memory" in error_msg or "oom" in error_msg:
            RecoveryStrategies.memory_recovery(job)
        
        # 파일 손상 문제
        elif "corrupt" in error_msg or "invalid" in error_msg:
            RecoveryStrategies.file_corruption_recovery(job)
    
    retry_manager.add_recovery_callback(recovery_callback)


# 시스템 초기화 함수
def initialize_retry_system() -> None:
    """재시도 시스템 초기화"""
    try:
        setup_retry_system()
        register_recovery_strategies()
        logging.info("Encoding retry system initialized")
    except Exception as e:
        logging.error(f"Failed to initialize retry system: {e}")


def shutdown_retry_system() -> None:
    """재시도 시스템 종료"""
    try:
        cleanup_retry_system()
        logging.info("Encoding retry system shutdown")
    except Exception as e:
        logging.error(f"Failed to shutdown retry system: {e}")


# 헬스체크 함수
def get_retry_health() -> Dict[str, any]:
    """재시도 시스템 헬스체크"""
    try:
        stats = get_retry_stats()
        
        health_status = "healthy"
        
        # 최근 실패가 많으면 경고
        if stats["recent_failures_1h"] > 10:
            health_status = "degraded"
        
        # 스케줄러 상태 확인
        if not retry_manager.scheduler_running:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "scheduler_running": retry_manager.scheduler_running,
            "failure_stats": stats,
            "retry_policy": {
                "max_retries": retry_manager.retry_policy.max_retries,
                "base_delay": retry_manager.retry_policy.base_delay,
                "max_delay": retry_manager.retry_policy.max_delay,
                "failure_threshold": retry_manager.retry_policy.failure_threshold
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
