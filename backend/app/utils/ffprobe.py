"""
Audio metadata extraction using ffprobe.

Returns a normalized dict with: duration, bitrate, sample_rate, channels, format
"""
from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Optional

from app.core.config import settings


def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """Extract basic audio metadata via ffprobe JSON output.

    Args:
        file_path: Path to a local media file

    Returns:
        dict: { duration, bitrate, sample_rate, channels, format }
    """
    cmd = [
        settings.FFPROBE_PATH,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]
    out = subprocess.check_output(cmd)
    data = json.loads(out.decode("utf-8"))

    # Defaults
    duration = 0
    bitrate = None
    sample_rate = None
    channels = None
    fmt = None

    # Prefer audio stream info if present
    streams = data.get("streams", []) or []
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if audio_stream:
        # duration might be on format or stream level
        if audio_stream.get("duration"):
            try:
                duration = int(float(audio_stream["duration"]))
            except Exception:
                pass
        if audio_stream.get("bit_rate"):
            try:
                bitrate = int(audio_stream["bit_rate"]) // 1000
            except Exception:
                pass
        if audio_stream.get("sample_rate"):
            try:
                sample_rate = int(audio_stream["sample_rate"])
            except Exception:
                pass
        if audio_stream.get("channels"):
            try:
                channels = int(audio_stream["channels"])
            except Exception:
                pass
        fmt = audio_stream.get("codec_name")

    # Fallback to format section
    fmt_section = data.get("format") or {}
    if not duration and fmt_section.get("duration"):
        try:
            duration = int(float(fmt_section["duration"]))
        except Exception:
            pass
    if not bitrate and fmt_section.get("bit_rate"):
        try:
            bitrate = int(fmt_section["bit_rate"]) // 1000
        except Exception:
            pass
    if not fmt and fmt_section.get("format_name"):
        fmt = fmt_section.get("format_name")

    return {
        "duration": duration,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "channels": channels,
        "format": fmt,
    }


