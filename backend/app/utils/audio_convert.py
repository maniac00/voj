"""FFmpeg 기반 오디오 변환 유틸리티.

convert_to_m4a / get_audio_duration 모두 blocking I/O이므로
호출부에서 asyncio.to_thread()로 감싸서 사용할 것.
"""
from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


def convert_to_m4a(input_path: str, output_path: str) -> bool:
    """input_path의 오디오를 AAC M4A로 변환하여 output_path에 저장한다.

    Returns:
        True on success, False on failure.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            logger.error("ffmpeg convert failed: %s", result.stderr[-500:] if result.stderr else "")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg convert timed out for %s", input_path)
        return False
    except FileNotFoundError:
        logger.error("ffmpeg not found on PATH")
        return False


def get_audio_duration(file_path: str) -> int:
    """ffprobe로 오디오 duration(초)을 추출한다.

    Returns:
        Duration in seconds (rounded). 0 on failure.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        file_path,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            logger.warning("ffprobe failed for %s: %s", file_path, result.stderr[:200] if result.stderr else "")
            return 0
        raw = result.stdout.strip()
        if not raw:
            return 0
        return round(float(raw))
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
        logger.warning("ffprobe duration extraction failed: %s", e)
        return 0
