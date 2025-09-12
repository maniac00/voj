import sys
import os


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.storage.base import BaseStorageService  # noqa: E402


def test_generate_key_standard_format():
    class _Dummy(BaseStorageService):
        async def upload_file(self, *a, **k):
            ...
        async def download_file(self, *a, **k):
            ...
        async def delete_file(self, *a, **k):
            ...
        async def file_exists(self, *a, **k):
            ...
        async def get_file_info(self, *a, **k):
            ...
        async def list_files(self, *a, **k):
            ...
        async def get_download_url(self, *a, **k):
            ...
        async def get_upload_url(self, *a, **k):
            ...

    d = _Dummy()
    key = d.generate_key(user_id="u1", book_id="b1", filename="001 Intro.wav", prefix="uploads")
    assert key == "book/b1/uploads/001_Intro.wav"

    key2 = d.generate_key(user_id="u1", book_id="b1", filename="001.m4a", prefix="media")
    assert key2 == "book/b1/media/001.m4a"

