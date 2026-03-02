"""Audio metadata extraction using mutagen (pure Python).

ffprobe가 없는 환경에서도 duration/bitrate/sample_rate/channels를 추출할 수 있다.
mutagen import 실패 시 기존 스텁 동작(기본값 반환)으로 graceful fallback.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import mutagen  # type: ignore[import-untyped]

    _HAS_MUTAGEN = True
except ImportError:
    _HAS_MUTAGEN = False
    logger.warning("mutagen not installed — audio metadata extraction will return defaults")

_DEFAULTS: Dict[str, Any] = {
    "duration": None,
    "bitrate": None,
    "sample_rate": None,
    "channels": None,
}


def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """Return audio metadata from *file_path*.

    mutagen을 사용하여 duration, bitrate, sample_rate, channels를 추출한다.
    mutagen이 없거나 파싱 실패 시 확장자 기반 기본값을 반환한다.
    """
    extension = Path(file_path).suffix.lstrip(".").lower() or None
    metadata: Dict[str, Any] = dict(_DEFAULTS)
    metadata["format"] = extension

    if not _HAS_MUTAGEN:
        return metadata

    try:
        audio = mutagen.File(file_path)  # type: ignore[union-attr]
        if audio is None:
            return metadata

        if audio.info is not None:
            info = audio.info
            if hasattr(info, "length") and info.length:
                metadata["duration"] = round(info.length)
            if hasattr(info, "bitrate") and info.bitrate:
                metadata["bitrate"] = info.bitrate
            if hasattr(info, "sample_rate") and info.sample_rate:
                metadata["sample_rate"] = info.sample_rate
            if hasattr(info, "channels") and info.channels:
                metadata["channels"] = info.channels
    except Exception as exc:
        logger.warning("mutagen failed to parse %s: %s", file_path, exc)

    return metadata


def extract_duration_from_bytes(data: bytes, suffix: str = ".m4a") -> Optional[int]:
    """바이트 데이터에서 duration(초)을 추출한다.

    임시 파일을 생성하여 mutagen으로 파싱한 뒤 삭제한다.
    실패 시 None을 반환한다.
    """
    if not _HAS_MUTAGEN:
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        audio = mutagen.File(tmp_path)  # type: ignore[union-attr]
        if audio is not None and audio.info is not None and hasattr(audio.info, "length") and audio.info.length:
            return round(audio.info.length)
    except Exception as exc:
        logger.warning("extract_duration_from_bytes failed: %s", exc)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return None


__all__ = ["extract_audio_metadata", "extract_duration_from_bytes"]
