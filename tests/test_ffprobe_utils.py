import sys
import os
import subprocess
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.utils.ffprobe import extract_audio_metadata  # noqa: E402
from app.core.config import settings  # noqa: E402


@pytest.mark.skipif(not os.path.exists(settings.FFPROBE_PATH), reason="ffprobe not available")
def test_extract_audio_metadata_with_synthetic_file(tmp_path):
    # generate a short silent audio if ffmpeg available
    if not os.path.exists(settings.FFMPEG_PATH):
        pytest.skip("ffmpeg not available")

    out_path = os.path.join(tmp_path, "test.mp4")
    cmd = [
        settings.FFMPEG_PATH,
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono",
        "-t",
        "1",
        "-c:a",
        "aac",
        "-b:a",
        "56k",
        out_path,
        "-y",
    ]
    subprocess.check_call(cmd)

    meta = extract_audio_metadata(out_path)
    assert meta["duration"] >= 0
    assert meta["sample_rate"] in (44100, None)
    assert meta["channels"] in (1, None)

