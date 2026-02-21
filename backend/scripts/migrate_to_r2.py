#!/usr/bin/env python3
"""
오디오 파일 R2 마이그레이션 스크립트
Railway 로컬 볼륨(/data/storage)의 오디오 파일을 Cloudflare R2로 업로드한다.

사용법:
    railway run python scripts/migrate_to_r2.py [--dry-run] [--prefix book/]

옵션:
    --dry-run   실제 업로드 없이 대상 파일 목록만 출력
    --prefix    특정 prefix의 파일만 마이그레이션 (기본: 전체)
"""
import argparse
import os
import sys

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError


def get_settings():
    from app.core.config import settings
    return settings


def get_db():
    from app.models.database import SessionLocal
    return SessionLocal()


def get_all_audio_keys(db) -> list:
    """DB에서 모든 오디오 챕터의 audio_key를 조회한다."""
    from app.models.audio_chapter_sql import AudioChapterSQL
    rows = db.query(AudioChapterSQL.audio_key).filter(
        AudioChapterSQL.audio_key.isnot(None)
    ).all()
    return [row.audio_key.lstrip("/") for row in rows if row.audio_key]


def get_local_storage_path(settings) -> str:
    """로컬 스토리지 루트 경로를 반환한다."""
    from app.services.storage.local import LocalStorageService
    svc = LocalStorageService()
    return svc.base_path


def build_r2_client(settings):
    endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="auto",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    )


def file_exists_in_r2(s3, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def get_content_type(filename: str) -> str:
    ext = os.path.splitext(filename.lower())[1]
    return {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".flac": "audio/flac",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
    }.get(ext, "application/octet-stream")


def main():
    parser = argparse.ArgumentParser(description="오디오 파일 R2 마이그레이션")
    parser.add_argument("--dry-run", action="store_true", help="업로드 없이 목록만 출력")
    parser.add_argument("--prefix", default="", help="특정 prefix 필터 (예: book/)")
    args = parser.parse_args()

    settings = get_settings()

    # 환경변수 검증
    missing = [v for v in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
               if not getattr(settings, v, "")]
    if missing:
        print(f"[ERROR] 필수 환경변수 미설정: {', '.join(missing)}")
        print("Railway 대시보드에서 환경변수를 설정한 후 다시 실행하세요.")
        sys.exit(1)

    print(f"[INFO] R2 버킷: {settings.R2_BUCKET_NAME}")
    print(f"[INFO] 계정 ID: {settings.R2_ACCOUNT_ID}")

    db = get_db()
    try:
        audio_keys = get_all_audio_keys(db)
    finally:
        db.close()

    if args.prefix:
        audio_keys = [k for k in audio_keys if k.startswith(args.prefix)]

    print(f"[INFO] DB 오디오 챕터 수: {len(audio_keys)}")

    local_root = get_local_storage_path(settings)
    print(f"[INFO] 로컬 스토리지 경로: {local_root}")

    if args.dry_run:
        print("\n[DRY RUN] 마이그레이션 대상 파일:")
        for key in audio_keys:
            local_path = os.path.join(local_root, key)
            exists = os.path.exists(local_path)
            size = os.path.getsize(local_path) if exists else 0
            print(f"  {'✓' if exists else '✗'} {key} ({size:,} bytes)")
        return

    s3 = build_r2_client(settings)
    bucket = settings.R2_BUCKET_NAME

    # R2 버킷 접근 확인
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"[INFO] R2 버킷 '{bucket}' 접근 확인 완료")
    except ClientError as e:
        print(f"[ERROR] R2 버킷 접근 실패: {e}")
        sys.exit(1)

    success = 0
    skip = 0
    fail = 0

    for i, key in enumerate(audio_keys, 1):
        local_path = os.path.join(local_root, key)
        print(f"[{i}/{len(audio_keys)}] {key}", end=" ... ")

        if not os.path.exists(local_path):
            print("SKIP (로컬 파일 없음)")
            skip += 1
            continue

        # R2에 이미 존재하는 경우 건너뜀
        if file_exists_in_r2(s3, bucket, key):
            file_size = os.path.getsize(local_path)
            print(f"SKIP (R2에 이미 존재, {file_size:,} bytes)")
            skip += 1
            continue

        try:
            file_size = os.path.getsize(local_path)
            content_type = get_content_type(local_path)
            with open(local_path, "rb") as f:
                s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=f,
                    ContentType=content_type,
                )
            print(f"OK ({file_size:,} bytes, {content_type})")
            success += 1
        except Exception as e:
            print(f"FAIL: {e}")
            fail += 1

    print(f"\n[완료] 성공: {success}, 건너뜀: {skip}, 실패: {fail}")
    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
