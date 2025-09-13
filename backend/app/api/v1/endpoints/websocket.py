"""
VOJ Audiobooks API - WebSocket 엔드포인트
실시간 로그 스트리밍 및 상태 업데이트
"""
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.services.websocket.log_streamer import log_streamer, LogLevel, LogCategory

router = APIRouter()


@router.websocket("/logs")
async def websocket_logs(
    websocket: WebSocket,
    chapter_id: Optional[str] = Query(None, description="구독할 챕터 ID"),
    connection_id: Optional[str] = Query(None, description="연결 ID")
):
    """
    실시간 로그 스트리밍 WebSocket
    - 전체 로그 또는 특정 챕터 로그 구독 가능
    - 양방향 통신으로 구독 관리
    """
    conn_id = await log_streamer.connect(websocket, connection_id)
    
    try:
        # 초기 챕터 구독 (쿼리 파라미터로 지정된 경우)
        if chapter_id:
            await log_streamer.subscribe_to_chapter(conn_id, chapter_id)
        
        # 클라이언트 메시지 처리 루프
        while True:
            try:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_client_message(conn_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": f"Message processing error: {str(e)}"
                }))
    
    except WebSocketDisconnect:
        pass
    finally:
        await log_streamer.disconnect(conn_id)


async def handle_client_message(connection_id: str, message: dict) -> None:
    """클라이언트 메시지 처리"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # 챕터 구독
        chapter_id = message.get("chapter_id")
        if chapter_id:
            await log_streamer.subscribe_to_chapter(connection_id, chapter_id)
    
    elif message_type == "unsubscribe":
        # 챕터 구독 해제
        chapter_id = message.get("chapter_id")
        if chapter_id:
            await log_streamer.unsubscribe_from_chapter(connection_id, chapter_id)
    
    elif message_type == "get_history":
        # 로그 히스토리 요청
        limit = message.get("limit", 50)
        await log_streamer.send_log_history(connection_id, limit)
    
    elif message_type == "ping":
        # 연결 확인
        await log_streamer.send_to_connection(connection_id, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    else:
        # 알 수 없는 메시지 타입
        await log_streamer.send_to_connection(connection_id, {
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })


@router.websocket("/status/{chapter_id}")
async def websocket_chapter_status(
    websocket: WebSocket,
    chapter_id: str,
    connection_id: Optional[str] = Query(None)
):
    """
    특정 챕터의 실시간 상태 업데이트 WebSocket
    - 인코딩 진행률, 상태 변경 등 실시간 알림
    """
    conn_id = await log_streamer.connect(websocket, connection_id)
    
    try:
        # 해당 챕터 자동 구독
        await log_streamer.subscribe_to_chapter(conn_id, chapter_id)
        
        # 현재 챕터 상태 전송
        await send_current_chapter_status(conn_id, chapter_id)
        
        # 클라이언트 메시지 처리
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "get_status":
                    await send_current_chapter_status(conn_id, chapter_id)
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except WebSocketDisconnect:
        pass
    finally:
        await log_streamer.disconnect(conn_id)


async def send_current_chapter_status(connection_id: str, chapter_id: str) -> None:
    """현재 챕터 상태 전송"""
    try:
        from app.models.audio_chapter import AudioChapter
        from app.services.encoding.encoding_queue import encoding_queue
        
        # 챕터 정보 조회
        chapter = AudioChapter.get_by_id(chapter_id)
        if not chapter:
            await log_streamer.send_to_connection(connection_id, {
                "type": "error",
                "message": f"Chapter {chapter_id} not found"
            })
            return
        
        # 인코딩 작업 정보 조회
        encoding_jobs = encoding_queue.get_jobs_by_chapter(chapter_id)
        current_job = None
        
        if encoding_jobs:
            # 가장 최근 작업 찾기
            current_job = max(encoding_jobs, key=lambda j: j.created_at)
        
        # 상태 정보 구성
        status_data = {
            "type": "chapter_status",
            "chapter_id": chapter_id,
            "chapter_status": chapter.status,
            "chapter_title": chapter.title,
            "file_name": chapter.file_info.original_name if chapter.file_info else None,
            "encoding_job": {
                "job_id": current_job.job_id,
                "status": current_job.status.value,
                "progress": current_job.progress,
                "retry_count": current_job.retry_count,
                "error_message": current_job.error_message
            } if current_job else None,
            "metadata": {
                "duration": chapter.audio_metadata.duration,
                "bitrate": chapter.audio_metadata.bitrate,
                "sample_rate": chapter.audio_metadata.sample_rate,
                "channels": chapter.audio_metadata.channels,
                "format": chapter.audio_metadata.format
            } if chapter.audio_metadata else None,
            "timestamp": datetime.now().isoformat()
        }
        
        await log_streamer.send_to_connection(connection_id, status_data)
        
    except Exception as e:
        await log_streamer.send_to_connection(connection_id, {
            "type": "error",
            "message": f"Failed to get chapter status: {str(e)}"
        })


# 편의 함수들
def log_upload_start(chapter_id: str, filename: str, file_size: int) -> None:
    """업로드 시작 로그"""
    log_streamer.add_log(
        level=LogLevel.INFO,
        category=LogCategory.UPLOAD,
        message=f"Upload started: {filename}",
        details={"file_size": file_size},
        chapter_id=chapter_id
    )


def log_upload_complete(chapter_id: str, filename: str) -> None:
    """업로드 완료 로그"""
    log_streamer.add_log(
        level=LogLevel.INFO,
        category=LogCategory.UPLOAD,
        message=f"Upload completed: {filename}",
        chapter_id=chapter_id
    )


def log_encoding_start(chapter_id: str, job_id: str, input_file: str) -> None:
    """인코딩 시작 로그"""
    log_streamer.add_log(
        level=LogLevel.INFO,
        category=LogCategory.ENCODING,
        message=f"Encoding started: {input_file}",
        chapter_id=chapter_id,
        job_id=job_id
    )


def log_encoding_progress(chapter_id: str, job_id: str, progress: float) -> None:
    """인코딩 진행률 로그"""
    log_streamer.add_log(
        level=LogLevel.INFO,
        category=LogCategory.ENCODING,
        message=f"Encoding progress: {progress:.1%}",
        details={"progress": progress},
        chapter_id=chapter_id,
        job_id=job_id
    )


def log_encoding_complete(chapter_id: str, job_id: str, output_file: str, 
                         compression_ratio: float) -> None:
    """인코딩 완료 로그"""
    log_streamer.add_log(
        level=LogLevel.INFO,
        category=LogCategory.ENCODING,
        message=f"Encoding completed: {output_file}",
        details={"compression_ratio": compression_ratio},
        chapter_id=chapter_id,
        job_id=job_id
    )


def log_encoding_error(chapter_id: str, job_id: str, error_message: str) -> None:
    """인코딩 에러 로그"""
    log_streamer.add_log(
        level=LogLevel.ERROR,
        category=LogCategory.ERROR,
        message=f"Encoding failed: {error_message}",
        chapter_id=chapter_id,
        job_id=job_id
    )
