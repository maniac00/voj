"""
VOJ Audiobooks API - Cloudflare R2 스토리지 서비스
S3-compatible API (boto3)를 통해 R2에 접근하며,
다운로드 URL은 R2 Worker HMAC 서명 URL을 반환한다.
"""
import asyncio
import functools
import hashlib
import hmac
import time
from typing import BinaryIO, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings

from .base import BaseStorageService, FileInfo, UploadResult


class R2StorageService(BaseStorageService):
    """Cloudflare R2 스토리지 서비스 (S3-compatible API)"""

    def __init__(self):
        self.bucket_name = settings.R2_BUCKET_NAME
        self.account_id = settings.R2_ACCOUNT_ID
        self.worker_url = settings.R2_WORKER_URL.rstrip("/")
        self.auth_secret = settings.R2_AUTH_SECRET

        endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name="auto",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        )

    def _run_async(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    def _sign_worker_url(self, key: str, expires_in: int = 3600) -> str:
        """R2 Worker HMAC 서명 URL 생성.
        Worker 검증 로직: message = "{key}:{exp_unix}", token = HMAC-SHA256 hex
        """
        exp = int(time.time()) + expires_in
        message = f"{key}:{exp}".encode()
        secret = self.auth_secret.encode()
        token = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return f"{self.worker_url}/{key}?token={token}&exp={exp}"

    async def upload_file(
        self,
        file_data: BinaryIO,
        key: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        try:
            upload_args: Dict = {
                "Bucket": self.bucket_name,
                "Key": key,
                "Body": file_data,
                "ContentType": content_type,
            }
            if metadata:
                upload_args["Metadata"] = metadata

            await self._run_async(self.s3_client.put_object, **upload_args)

            file_info = await self.get_file_info(key)
            file_size = file_info.size if file_info else 0

            return UploadResult(
                success=True,
                key=key,
                size=file_size,
                url=f"{self.worker_url}/{key}",
            )
        except Exception as e:
            return UploadResult(success=False, key=key, size=0, error=str(e))

    async def download_file(self, key: str) -> Optional[bytes]:
        try:
            response = await self._run_async(
                self.s3_client.get_object, Bucket=self.bucket_name, Key=key
            )
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return None
            raise
        except Exception:
            return None

    async def delete_file(self, key: str) -> bool:
        try:
            await self._run_async(
                self.s3_client.delete_object, Bucket=self.bucket_name, Key=key
            )
            return True
        except Exception:
            return False

    async def file_exists(self, key: str) -> bool:
        try:
            await self._run_async(
                self.s3_client.head_object, Bucket=self.bucket_name, Key=key
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise
        except Exception:
            return False

    async def get_file_info(self, key: str) -> Optional[FileInfo]:
        try:
            response = await self._run_async(
                self.s3_client.head_object, Bucket=self.bucket_name, Key=key
            )
            return FileInfo(
                key=key,
                size=response.get("ContentLength", 0),
                content_type=response.get("ContentType", "application/octet-stream"),
                etag=response.get("ETag", "").strip('"'),
                last_modified=response.get("LastModified").isoformat()
                if response.get("LastModified")
                else None,
                metadata=response.get("Metadata", {}),
            )
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return None
            raise
        except Exception:
            return None

    async def list_files(self, prefix: str = "", limit: int = 100) -> List[FileInfo]:
        try:
            response = await self._run_async(
                self.s3_client.list_objects_v2,
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit,
            )
            files = []
            for obj in response.get("Contents", []):
                files.append(
                    FileInfo(
                        key=obj["Key"],
                        size=obj["Size"],
                        content_type=self.get_content_type(obj["Key"]),
                        etag=obj.get("ETag", "").strip('"'),
                        last_modified=obj.get("LastModified").isoformat()
                        if obj.get("LastModified")
                        else None,
                    )
                )
            return files
        except Exception:
            return []

    async def get_download_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """R2 Worker HMAC 서명 URL 반환 (이그레스 무료 + CDN)"""
        if not self.worker_url or not self.auth_secret:
            return None
        return self._sign_worker_url(key, expires_in)

    async def get_upload_url(
        self, key: str, content_type: str, expires_in: int = 3600
    ) -> Optional[str]:
        """R2 S3-compatible Pre-signed 업로드 URL"""
        try:
            url = await self._run_async(
                self.s3_client.generate_presigned_url,
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            return url
        except Exception:
            return None

    async def health_check(self) -> Dict:
        try:
            await self._run_async(self.s3_client.head_bucket, Bucket=self.bucket_name)
            return {
                "status": "healthy",
                "bucket": self.bucket_name,
                "account_id": self.account_id,
            }
        except NoCredentialsError:
            return {"status": "unhealthy", "error": "No R2 credentials found"}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            return {"status": "unhealthy", "error": f"R2 error: {error_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
