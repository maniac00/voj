"""Lightweight audio metadata helpers that avoid external FFmpeg/ffprobe dependencies."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


_DEFAULTS: Dict[str, Any] = {
    "duration": None,
    "bitrate": None,
    "sample_rate": None,
    "channels": None,
}


def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """Return best-effort metadata using only filename hints.

    The current MVP는 인코딩/트랜스코딩 기능을 사용하지 않으므로, FFmpeg/ffprobe에 의존하지 않고
    확장자 기반으로 format 정도만 식별한다. 나머지 필드는 기본값으로 채운다.
    """
    extension = Path(file_path).suffix.lstrip(".").lower() or None

    metadata = dict(_DEFAULTS)
    metadata["format"] = extension
    return metadata


__all__ = ["extract_audio_metadata"]
