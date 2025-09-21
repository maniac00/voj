"""
WebSocket 기반 실시간 로그 스트리밍 서비스
"""
from __future__ import annotations

import json
import asyncio
import logging
from typing import Dict, Set, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import threading

from fastapi import WebSocket, WebSocketDisconnect


class LogLevel(Enum):
    """로그 레벨"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(Enum):
    """로그 카테고리"""
    UPLOAD = "upload"
    PROCESSING = "processing"
    SYSTEM = "system"
    ERROR = "error"


@dataclass
class LogMessage:
    """로그 메시지"""
    id: str
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    details: Optional[Dict[str, Any]] = None
    chapter_id: Optional[str] = None
    book_id: Optional[str] = None
    job_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        data['category'] = self.category.value
        return data


class WebSocketLogStreamer:
    """WebSocket 로그 스트리머"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # connection_id -> {chapter_ids}
        self.log_history: List[LogMessage] = []
        self.max_history = 1000
        self.lock = threading.Lock()
        
        # 로그 핸들러 설정
        self.log_handler = WebSocketLogHandler(self)
        self.logger = logging.getLogger("voj.websocket")
    
    async def connect(self, websocket: WebSocket, connection_id: Optional[str] = None) -> str:
        """WebSocket 연결"""
        await websocket.accept()
        
        if not connection_id:
            connection_id = str(uuid.uuid4())
        
        with self.lock:
            self.connections[connection_id] = websocket
            self.subscriptions[connection_id] = set()
        
        # 연결 환영 메시지
        await self.send_to_connection(connection_id, {
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "message": "WebSocket log streaming connected"
        })
        
        # 최근 로그 히스토리 전송
        await self.send_log_history(connection_id)
        
        self.logger.info(f"WebSocket connected: {connection_id}")
        return connection_id
    
    async def disconnect(self, connection_id: str) -> None:
        """WebSocket 연결 해제"""
        with self.lock:
            if connection_id in self.connections:
                del self.connections[connection_id]
            if connection_id in self.subscriptions:
                del self.subscriptions[connection_id]
        
        self.logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def subscribe_to_chapter(self, connection_id: str, chapter_id: str) -> None:
        """특정 챕터 로그 구독"""
        with self.lock:
            if connection_id in self.subscriptions:
                self.subscriptions[connection_id].add(chapter_id)
        
        await self.send_to_connection(connection_id, {
            "type": "subscription",
            "action": "subscribed",
            "chapter_id": chapter_id,
            "message": f"Subscribed to chapter {chapter_id} logs"
        })
    
    async def unsubscribe_from_chapter(self, connection_id: str, chapter_id: str) -> None:
        """챕터 로그 구독 해제"""
        with self.lock:
            if connection_id in self.subscriptions:
                self.subscriptions[connection_id].discard(chapter_id)
        
        await self.send_to_connection(connection_id, {
            "type": "subscription", 
            "action": "unsubscribed",
            "chapter_id": chapter_id,
            "message": f"Unsubscribed from chapter {chapter_id} logs"
        })
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """특정 연결로 메시지 전송"""
        with self.lock:
            websocket = self.connections.get(connection_id)
        
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                self.logger.error(f"Failed to send message to {connection_id}: {e}")
                # 연결 정리
                await self.disconnect(connection_id)
        
        return False
    
    async def broadcast_log(self, log_message: LogMessage) -> None:
        """로그 메시지 브로드캐스트"""
        # 로그 히스토리에 추가
        with self.lock:
            self.log_history.append(log_message)
            
            # 히스토리 크기 제한
            if len(self.log_history) > self.max_history:
                self.log_history = self.log_history[-self.max_history:]
        
        # 관련 연결들에게 전송
        message_data = {
            "type": "log",
            "data": log_message.to_dict()
        }
        
        connections_to_send = []
        
        with self.lock:
            for connection_id, subscribed_chapters in self.subscriptions.items():
                # 전체 구독 또는 해당 챕터 구독
                if (not subscribed_chapters or 
                    (log_message.chapter_id and log_message.chapter_id in subscribed_chapters)):
                    connections_to_send.append(connection_id)
        
        # 비동기적으로 메시지 전송
        for connection_id in connections_to_send:
            await self.send_to_connection(connection_id, message_data)
    
    async def send_log_history(self, connection_id: str, limit: int = 50) -> None:
        """로그 히스토리 전송"""
        with self.lock:
            recent_logs = self.log_history[-limit:] if self.log_history else []
        
        if recent_logs:
            history_data = {
                "type": "history",
                "logs": [log.to_dict() for log in recent_logs],
                "count": len(recent_logs)
            }
            
            await self.send_to_connection(connection_id, history_data)
    
    def add_log(self, level: LogLevel, category: LogCategory, message: str,
                details: Optional[Dict[str, Any]] = None, chapter_id: Optional[str] = None,
                book_id: Optional[str] = None, job_id: Optional[str] = None) -> None:
        """로그 메시지 추가 (동기 버전)"""
        log_message = LogMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            level=level,
            category=category,
            message=message,
            details=details,
            chapter_id=chapter_id,
            book_id=book_id,
            job_id=job_id
        )
        
        # 비동기 브로드캐스트를 위한 태스크 생성
        asyncio.create_task(self.broadcast_log(log_message))
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계"""
        with self.lock:
            total_connections = len(self.connections)
            total_subscriptions = sum(len(subs) for subs in self.subscriptions.values())
            
            return {
                "total_connections": total_connections,
                "total_subscriptions": total_subscriptions,
                "log_history_size": len(self.log_history),
                "max_history": self.max_history
            }


class WebSocketLogHandler(logging.Handler):
    """로깅 시스템과 WebSocket 연동을 위한 핸들러"""
    
    def __init__(self, streamer: WebSocketLogStreamer):
        super().__init__()
        self.streamer = streamer
        self.setLevel(logging.INFO)
    
    def emit(self, record: logging.LogRecord) -> None:
        """로그 레코드를 WebSocket으로 전송"""
        try:
            # 로그 레벨 매핑
            level_mapping = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.CRITICAL
            }
            
            level = level_mapping.get(record.levelno, LogLevel.INFO)
            
            # 카테고리 추출 (로거 이름에서)
            category = LogCategory.SYSTEM
            if "upload" in record.name:
                category = LogCategory.UPLOAD
            elif "processing" in record.name:
                category = LogCategory.PROCESSING
            elif record.levelno >= logging.ERROR:
                category = LogCategory.ERROR
            
            # 추가 정보 추출
            details = {}
            if hasattr(record, 'chapter_id'):
                details['chapter_id'] = record.chapter_id
            if hasattr(record, 'book_id'):
                details['book_id'] = record.book_id
            if hasattr(record, 'job_id'):
                details['job_id'] = record.job_id
            
            # WebSocket으로 전송
            self.streamer.add_log(
                level=level,
                category=category,
                message=record.getMessage(),
                details=details if details else None,
                chapter_id=getattr(record, 'chapter_id', None),
                book_id=getattr(record, 'book_id', None),
                job_id=getattr(record, 'job_id', None)
            )
            
        except Exception as e:
            # 로그 핸들러에서 예외 발생 시 무시 (무한 루프 방지)
            print(f"WebSocket log handler error: {e}")


# 전역 로그 스트리머
log_streamer = WebSocketLogStreamer()


def setup_websocket_logging() -> None:
    """WebSocket 로깅 설정"""
    # 루트 로거에 WebSocket 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(log_streamer.log_handler)
    
    # 특정 로거들에 WebSocket 핸들러 추가
    loggers_to_stream = [
        "app.api.v1.endpoints.files",
        "app.api.v1.endpoints.audio"
    ]
    
    for logger_name in loggers_to_stream:
        logger = logging.getLogger(logger_name)
        logger.addHandler(log_streamer.log_handler)
        logger.setLevel(logging.INFO)


def add_upload_log(message: str, level: LogLevel = LogLevel.INFO,
                  chapter_id: Optional[str] = None, book_id: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None) -> None:
    """업로드 로그 추가 (편의 함수)"""
    log_streamer.add_log(
        level=level,
        category=LogCategory.UPLOAD,
        message=message,
        details=details,
        chapter_id=chapter_id,
        book_id=book_id
    )


def add_error_log(message: str, chapter_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None) -> None:
    """에러 로그 추가 (편의 함수)"""
    log_streamer.add_log(
        level=LogLevel.ERROR,
        category=LogCategory.ERROR,
        message=message,
        details=details,
        chapter_id=chapter_id
    )


def get_log_streamer_stats() -> Dict[str, Any]:
    """로그 스트리머 통계 (편의 함수)"""
    return log_streamer.get_connection_stats()
