"""
인코딩 작업 큐 및 상태 관리 서비스
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
import uuid
import threading
import queue
import logging

from app.core.config import settings
from app.services.encoding.ffmpeg_service import FFmpegEncodingService, EncodingResult
from app.models.audio_chapter import AudioChapter
from app.services.encoding.file_manager import file_manager


class EncodingStatus(Enum):
    """인코딩 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EncodingJob:
    """인코딩 작업"""
    job_id: str
    chapter_id: str
    book_id: str
    input_path: str
    output_path: str
    status: EncodingStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Optional[Dict[str, Any]] = None
    progress: float = 0.0  # 0.0 ~ 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


class EncodingQueue:
    """인코딩 작업 큐 관리자"""
    
    def __init__(self, max_workers: Optional[int] = None):
        # 환경별 설정 적용
        from app.services.encoding.environment_config import get_current_environment_config
        env_config = get_current_environment_config()
        
        self.max_workers = max_workers or env_config.max_workers
        self.jobs: Dict[str, EncodingJob] = {}
        self.job_queue: queue.Queue = queue.Queue()
        self.workers: List[threading.Thread] = []
        self.running = False
        self.lock = threading.Lock()
        
        # 환경별 FFmpeg 서비스 설정
        self.ffmpeg_service = FFmpegEncodingService(env_config.encoding_config)
        
        self.status_callbacks: List[Callable[[EncodingJob], None]] = []
        
        # 환경별 로깅 설정
        self.logger = logging.getLogger(__name__)
        if env_config.enable_detailed_logging:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def add_status_callback(self, callback: Callable[[EncodingJob], None]) -> None:
        """상태 변경 콜백 추가"""
        self.status_callbacks.append(callback)
    
    def _notify_status_change(self, job: EncodingJob) -> None:
        """상태 변경 알림"""
        for callback in self.status_callbacks:
            try:
                callback(job)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
    
    def start(self) -> None:
        """큐 처리 시작"""
        if self.running:
            return
        
        self.running = True
        
        # 워커 스레드 시작
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, name=f"EncodingWorker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"Encoding queue started with {self.max_workers} workers")
    
    def stop(self) -> None:
        """큐 처리 중지"""
        self.running = False
        
        # 모든 워커에 중지 신호 전송
        for _ in self.workers:
            self.job_queue.put(None)
        
        # 워커 스레드 종료 대기
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        self.logger.info("Encoding queue stopped")
    
    def submit_job(self, chapter_id: str, book_id: str, input_path: str, output_path: str) -> str:
        """인코딩 작업 제출"""
        job_id = str(uuid.uuid4())
        
        job = EncodingJob(
            job_id=job_id,
            chapter_id=chapter_id,
            book_id=book_id,
            input_path=input_path,
            output_path=output_path,
            status=EncodingStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        with self.lock:
            self.jobs[job_id] = job
            self.job_queue.put(job_id)
        
        self.logger.info(f"Encoding job submitted: {job_id} for chapter {chapter_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[EncodingJob]:
        """작업 조회"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def get_jobs_by_status(self, status: EncodingStatus) -> List[EncodingJob]:
        """상태별 작업 조회"""
        with self.lock:
            return [job for job in self.jobs.values() if job.status == status]
    
    def get_jobs_by_chapter(self, chapter_id: str) -> List[EncodingJob]:
        """챕터별 작업 조회"""
        with self.lock:
            return [job for job in self.jobs.values() if job.chapter_id == chapter_id]
    
    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job.status == EncodingStatus.PENDING:
                job.status = EncodingStatus.CANCELLED
                self._notify_status_change(job)
                return True
        return False
    
    def retry_job(self, job_id: str) -> bool:
        """작업 재시도"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job.status == EncodingStatus.FAILED and job.retry_count < job.max_retries:
                job.status = EncodingStatus.PENDING
                job.retry_count += 1
                job.error_message = None
                job.progress = 0.0
                self.job_queue.put(job_id)
                self._notify_status_change(job)
                return True
        return False
    
    def _worker(self) -> None:
        """워커 스레드 메인 루프"""
        while self.running:
            try:
                # 작업 대기 (1초 타임아웃)
                job_id = self.job_queue.get(timeout=1)
                
                if job_id is None:  # 중지 신호
                    break
                
                # 작업 처리
                self._process_job(job_id)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
    
    def _process_job(self, job_id: str) -> None:
        """개별 작업 처리"""
        with self.lock:
            job = self.jobs.get(job_id)
            if not job or job.status != EncodingStatus.PENDING:
                return
            
            job.status = EncodingStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)
            job.progress = 0.1
        
        self._notify_status_change(job)
        
        try:
            # 파일 경로 및 디렉토리 준비
            self.logger.info(f"Starting encoding job {job_id}: {job.input_path} -> {job.output_path}")
            
            # 필요한 디렉토리 생성
            file_manager.ensure_directories(job.book_id)
            
            # 입력 파일 존재 확인
            if not os.path.exists(job.input_path):
                raise FileNotFoundError(f"Input file not found: {job.input_path}")
            
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(job.output_path), exist_ok=True)
            
            # 진행률 업데이트 (30%)
            job.progress = 0.3
            self._notify_status_change(job)
            
            # 파일 무결성 확인
            is_valid, integrity_error = file_manager.validate_file_integrity(job.input_path)
            if not is_valid:
                raise ValueError(f"Input file integrity check failed: {integrity_error}")
            
            # 진행률 업데이트 (50%)
            job.progress = 0.5
            self._notify_status_change(job)
            
            # FFmpeg 인코딩
            encoding_result = self.ffmpeg_service.encode_audio(job.input_path, job.output_path)
            
            # 진행률 업데이트 (80%)
            job.progress = 0.8
            self._notify_status_change(job)
            
            if encoding_result.success:
                # 인코딩 성공 - 결과 파일 검증
                is_valid, validation_error = file_manager.validate_file_integrity(job.output_path)
                if not is_valid:
                    raise ValueError(f"Encoded file validation failed: {validation_error}")
                
                # 성공 처리
                job.status = EncodingStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                job.progress = 1.0
                job.metadata = encoding_result.metadata
                
                self.logger.info(
                    f"Encoding job {job_id} completed successfully: "
                    f"{encoding_result.original_size} -> {encoding_result.encoded_size} bytes "
                    f"({encoding_result.processing_time:.2f}s)"
                )
                
                # AudioChapter 업데이트
                self._update_chapter_on_success(job, encoding_result)
                
                # 임시 파일 정리
                file_manager.cleanup_temp_files(job.book_id, job.chapter_id)
                
            else:
                # 실패 처리
                job.status = EncodingStatus.FAILED
                job.error_message = encoding_result.error
                
                self.logger.error(f"Encoding job {job_id} failed: {encoding_result.error}")
                
                # AudioChapter 에러 상태 업데이트
                self._update_chapter_on_failure(job)
                
                # 실패한 출력 파일 정리
                if os.path.exists(job.output_path):
                    try:
                        os.remove(job.output_path)
                    except Exception:
                        pass
        
        except Exception as e:
            # 예외 처리
            job.status = EncodingStatus.FAILED
            job.error_message = f"Processing error: {str(e)}"
            
            self.logger.error(f"Encoding job {job_id} failed with exception: {e}")
            self._update_chapter_on_failure(job)
            
            # 실패 시 정리
            try:
                file_manager.cleanup_temp_files(job.book_id, job.chapter_id)
                if os.path.exists(job.output_path):
                    os.remove(job.output_path)
            except Exception:
                pass
        
        finally:
            self._notify_status_change(job)
    
    def _update_chapter_on_success(self, job: EncodingJob, result: EncodingResult) -> None:
        """인코딩 성공 시 AudioChapter 업데이트"""
        try:
            chapter = AudioChapter.get_by_id(job.chapter_id)
            if chapter and result.metadata:
                # 메타데이터로 처리 완료 표시
                chapter.mark_processing_completed(result.metadata)
                
                # 인코딩된 파일 정보 업데이트
                if chapter.file_info and result.output_path:
                    # 인코딩 결과 파일 경로 저장
                    if settings.ENVIRONMENT == "local":
                        chapter.file_info.local_path = result.output_path
                    else:
                        chapter.file_info.s3_key = result.output_path
                    
                    chapter.save()
                    
                    # 원본 파일과 인코딩 파일 크기 비교 로깅
                    if result.original_size > 0 and result.encoded_size > 0:
                        compression_ratio = result.original_size / result.encoded_size
                        self.logger.info(
                            f"Encoding completed for chapter {job.chapter_id}: "
                            f"{result.original_size} → {result.encoded_size} bytes "
                            f"({compression_ratio:.2f}x compression)"
                        )
                
        except Exception as e:
            self.logger.error(f"Failed to update chapter {job.chapter_id}: {e}")
    
    def _update_chapter_on_failure(self, job: EncodingJob) -> None:
        """인코딩 실패 시 AudioChapter 업데이트"""
        try:
            chapter = AudioChapter.get_by_id(job.chapter_id)
            if chapter:
                chapter.mark_processing_error(job.error_message or "Encoding failed")
        except Exception as e:
            self.logger.error(f"Failed to update chapter {job.chapter_id} on failure: {e}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """큐 통계 조회"""
        with self.lock:
            status_counts = {}
            for status in EncodingStatus:
                status_counts[status.value] = len([j for j in self.jobs.values() if j.status == status])
            
            # 평균 처리 시간 계산
            completed_jobs = [j for j in self.jobs.values() if j.status == EncodingStatus.COMPLETED]
            avg_processing_time = 0.0
            
            if completed_jobs:
                total_time = sum(
                    (j.completed_at - j.started_at).total_seconds() 
                    for j in completed_jobs 
                    if j.started_at and j.completed_at
                )
                avg_processing_time = total_time / len(completed_jobs)
            
            return {
                "total_jobs": len(self.jobs),
                "status_counts": status_counts,
                "queue_size": self.job_queue.qsize(),
                "workers": len(self.workers),
                "avg_processing_time": avg_processing_time,
                "running": self.running
            }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """오래된 작업 정리"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        removed_count = 0
        
        with self.lock:
            job_ids_to_remove = []
            
            for job_id, job in self.jobs.items():
                if (job.status in [EncodingStatus.COMPLETED, EncodingStatus.FAILED, EncodingStatus.CANCELLED] and
                    job.created_at.timestamp() < cutoff_time):
                    job_ids_to_remove.append(job_id)
            
            for job_id in job_ids_to_remove:
                del self.jobs[job_id]
                removed_count += 1
        
        self.logger.info(f"Cleaned up {removed_count} old encoding jobs")
        return removed_count


# 전역 인코딩 큐 인스턴스
encoding_queue = EncodingQueue()


def start_encoding_queue() -> None:
    """인코딩 큐 시작 (편의 함수)"""
    encoding_queue.start()


def stop_encoding_queue() -> None:
    """인코딩 큐 중지 (편의 함수)"""
    encoding_queue.stop()


def submit_encoding_job(chapter_id: str, book_id: str, input_path: str, output_path: str) -> str:
    """인코딩 작업 제출 (편의 함수)"""
    return encoding_queue.submit_job(chapter_id, book_id, input_path, output_path)


def get_encoding_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """인코딩 작업 상태 조회 (편의 함수)"""
    job = encoding_queue.get_job(job_id)
    return job.to_dict() if job else None


def get_encoding_queue_stats() -> Dict[str, Any]:
    """인코딩 큐 통계 (편의 함수)"""
    return encoding_queue.get_queue_stats()


class EncodingStatusManager:
    """인코딩 상태 관리자 (실시간 상태 추적)"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.lock = threading.Lock()
    
    def subscribe(self, chapter_id: str, callback: Callable[[Dict[str, Any]], None]) -> str:
        """챕터별 상태 변경 구독"""
        subscription_id = str(uuid.uuid4())
        
        with self.lock:
            if chapter_id not in self.subscribers:
                self.subscribers[chapter_id] = []
            self.subscribers[chapter_id].append(callback)
        
        return subscription_id
    
    def unsubscribe(self, chapter_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """구독 해제"""
        with self.lock:
            if chapter_id in self.subscribers:
                try:
                    self.subscribers[chapter_id].remove(callback)
                    if not self.subscribers[chapter_id]:
                        del self.subscribers[chapter_id]
                except ValueError:
                    pass
    
    def notify_status_change(self, job: EncodingJob) -> None:
        """상태 변경 알림 전송"""
        status_data = {
            "job_id": job.job_id,
            "chapter_id": job.chapter_id,
            "status": job.status.value,
            "progress": job.progress,
            "error_message": job.error_message,
            "metadata": job.metadata
        }
        
        with self.lock:
            callbacks = self.subscribers.get(job.chapter_id, [])
            
        for callback in callbacks:
            try:
                callback(status_data)
            except Exception as e:
                self.logger.error(f"Status notification error: {e}")


# 전역 상태 관리자
status_manager = EncodingStatusManager()

# 인코딩 큐에 상태 관리자 연결
encoding_queue.add_status_callback(status_manager.notify_status_change)


def subscribe_to_encoding_status(chapter_id: str, callback: Callable[[Dict[str, Any]], None]) -> str:
    """인코딩 상태 구독 (편의 함수)"""
    return status_manager.subscribe(chapter_id, callback)


def unsubscribe_from_encoding_status(chapter_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
    """인코딩 상태 구독 해제 (편의 함수)"""
    status_manager.unsubscribe(chapter_id, callback)


# 애플리케이션 시작 시 인코딩 큐 자동 시작
def initialize_encoding_system() -> None:
    """인코딩 시스템 초기화"""
    try:
        start_encoding_queue()
        logging.info("Encoding system initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize encoding system: {e}")


# 애플리케이션 종료 시 정리
def cleanup_encoding_system() -> None:
    """인코딩 시스템 정리"""
    try:
        stop_encoding_queue()
        logging.info("Encoding system cleaned up successfully")
    except Exception as e:
        logging.error(f"Failed to cleanup encoding system: {e}")


# 헬스체크 함수
def get_encoding_health() -> Dict[str, Any]:
    """인코딩 시스템 헬스체크"""
    try:
        stats = get_encoding_queue_stats()
        
        # 헬스 상태 결정
        health_status = "healthy"
        
        # 실패한 작업이 많으면 경고
        failed_count = stats["status_counts"].get("failed", 0)
        total_count = stats["total_jobs"]
        
        if total_count > 0 and failed_count / total_count > 0.5:
            health_status = "degraded"
        
        # 큐가 중지되었으면 비정상
        if not stats["running"]:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "queue_running": stats["running"],
            "total_jobs": total_count,
            "failed_jobs": failed_count,
            "queue_size": stats["queue_size"],
            "workers": stats["workers"],
            "avg_processing_time": stats["avg_processing_time"]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
