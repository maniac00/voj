"""Compatibility module providing audio metadata helpers without FFmpeg/ffprobe."""
from __future__ import annotations

from .audio_metadata import extract_audio_metadata

__all__ = ["extract_audio_metadata"]
