"""
VOJ Audiobooks API - S3 스토리지 서비스
AWS S3를 사용한 스토리지 구현
"""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, BinaryIO, Dict, List
from datetime import datetime, timedelta
import asyncio
import functools

from app.core.config import settings
from .base import BaseStorageService, FileInfo, UploadResult


class S3StorageService(BaseStorageService):
    """AWS S3 스토리지 서비스"""
    
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        
        # S3 클라이언트 생성
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    def _run_async(self, func, *args, **kwargs):
        """동기 함수를 비동기로 실행"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    
    async def upload_file(
        self, 
        file_data: BinaryIO, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        """파일 업로드"""
        try:
            # 업로드 매개변수 준비
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': key,
                'Body': file_data,
                'ContentType': content_type,
            }
            
            if metadata:
                upload_args['Metadata'] = metadata
            
            # S3에 업로드
            await self._run_async(self.s3_client.put_object, **upload_args)
            
            # 파일 크기 확인
            file_info = await self.get_file_info(key)
            file_size = file_info.size if file_info else 0
            
            return UploadResult(
                success=True,
                key=key,
                size=file_size,
                url=f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            )
            
        except Exception as e:
            return UploadResult(
                success=False,
                key=key,
                size=0,
                error=str(e)
            )
    
    async def download_file(self, key: str) -> Optional[bytes]:
        """파일 다운로드"""
        try:
            response = await self._run_async(
                self.s3_client.get_object,
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise
        except Exception:
            return None
    
    async def delete_file(self, key: str) -> bool:
        """파일 삭제"""
        try:
            await self._run_async(
                self.s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except Exception:
            return False
    
    async def file_exists(self, key: str) -> bool:
        """파일 존재 여부 확인"""
        try:
            await self._run_async(
                self.s3_client.head_object,
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
        except Exception:
            return False
    
    async def get_file_info(self, key: str) -> Optional[FileInfo]:
        """파일 정보 조회"""
        try:
            response = await self._run_async(
                self.s3_client.head_object,
                Bucket=self.bucket_name,
                Key=key
            )
            
            return FileInfo(
                key=key,
                size=response.get('ContentLength', 0),
                content_type=response.get('ContentType', 'application/octet-stream'),
                etag=response.get('ETag', '').strip('"'),
                last_modified=response.get('LastModified').isoformat() if response.get('LastModified') else None,
                metadata=response.get('Metadata', {})
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise
        except Exception:
            return None
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[FileInfo]:
        """파일 목록 조회"""
        try:
            response = await self._run_async(
                self.s3_client.list_objects_v2,
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append(FileInfo(
                    key=obj['Key'],
                    size=obj['Size'],
                    content_type=self.get_content_type(obj['Key']),
                    etag=obj.get('ETag', '').strip('"'),
                    last_modified=obj.get('LastModified').isoformat() if obj.get('LastModified') else None
                ))
            
            return files
            
        except Exception:
            return []
    
    async def get_download_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """다운로드 URL 생성 (Pre-signed URL)"""
        try:
            url = await self._run_async(
                self.s3_client.generate_presigned_url,
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
            
        except Exception:
            return None
    
    async def get_upload_url(
        self, 
        key: str, 
        content_type: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """업로드 URL 생성 (Pre-signed URL)"""
        try:
            url = await self._run_async(
                self.s3_client.generate_presigned_url,
                'put_object',
                Params={
                    'Bucket': self.bucket_name, 
                    'Key': key,
                    'ContentType': content_type
                },
                ExpiresIn=expires_in
            )
            return url
            
        except Exception:
            return None
    
    async def get_cloudfront_signed_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """CloudFront Signed URL 생성"""
        try:
            if not settings.CLOUDFRONT_DOMAIN:
                return None
            
            from botocore.signers import CloudFrontSigner
            import rsa
            import os
            import boto3
            
            # 프라이빗 키 로드 (우선순위: Secrets Manager > 파일 경로)
            private_key_pem: Optional[bytes] = None
            secret_id = getattr(settings, 'CLOUDFRONT_PRIVATE_KEY_SECRET_ID', None)
            if secret_id:
                try:
                    sm = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
                    sec = sm.get_secret_value(SecretId=secret_id)
                    secret_string = sec.get('SecretString')
                    if secret_string:
                        private_key_pem = secret_string.encode('utf-8')
                    elif 'SecretBinary' in sec:
                        private_key_pem = sec['SecretBinary']
                except Exception:
                    private_key_pem = None
            if private_key_pem is None and getattr(settings, 'CLOUDFRONT_PRIVATE_KEY_PATH', None) and os.path.exists(settings.CLOUDFRONT_PRIVATE_KEY_PATH):
                with open(settings.CLOUDFRONT_PRIVATE_KEY_PATH, 'rb') as key_file:
                    private_key_pem = key_file.read()
            if not private_key_pem:
                return None
            private_key = rsa.PrivateKey.load_pkcs1(private_key_pem)
            
            def rsa_signer(message):
                return rsa.sign(message, private_key, 'SHA-1')
            
            # CloudFront URL
            url = f"https://{settings.CLOUDFRONT_DOMAIN}/{key}"
            
            # 만료 시간 설정
            expire_date = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Signed URL 생성
            cloudfront_signer = CloudFrontSigner(settings.CLOUDFRONT_KEY_PAIR_ID, rsa_signer)
            signed_url = cloudfront_signer.generate_presigned_url(url, date_less_than=expire_date)
            
            return signed_url
            
        except Exception as e:
            print(f"Error generating CloudFront signed URL: {e}")
            return None
    
    async def health_check(self) -> Dict[str, any]:
        """S3 연결 상태 확인"""
        try:
            # 버킷 존재 확인
            await self._run_async(
                self.s3_client.head_bucket,
                Bucket=self.bucket_name
            )
            
            # 버킷 위치 확인
            location = await self._run_async(
                self.s3_client.get_bucket_location,
                Bucket=self.bucket_name
            )
            
            return {
                "status": "healthy",
                "bucket": self.bucket_name,
                "region": location.get('LocationConstraint') or 'us-east-1'
            }
            
        except NoCredentialsError:
            return {
                "status": "unhealthy",
                "error": "No AWS credentials found"
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return {
                    "status": "unhealthy",
                    "error": f"Bucket {self.bucket_name} not found"
                }
            elif error_code == '403':
                return {
                    "status": "unhealthy",
                    "error": "Access denied to bucket"
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"S3 error: {error_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

