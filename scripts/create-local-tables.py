#!/usr/bin/env python3
"""
DynamoDB Local 테이블 생성 스크립트

설계 문서의 데이터 모델을 기반으로 로컬 개발용 DynamoDB 테이블을 생성합니다.
PynamoDB 모델 정의(Book, AudioChapter)를 직접 사용하여 테이블을 생성합니다.
"""

import boto3
import sys
import time
from pathlib import Path
from botocore.exceptions import ClientError, EndpointConnectionError

# backend 경로를 PYTHONPATH에 추가하여 app.* 모듈 임포트 가능하게 처리
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # type: ignore
from app.models.book import Book  # type: ignore
from app.models.audio_chapter import AudioChapter, FileInfo  # type: ignore


def create_dynamodb_client():
    """DynamoDB Local 클라이언트 생성"""
    return boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8001',
        region_name='ap-northeast-2',
        aws_access_key_id='local',
        aws_secret_access_key='local'
    )


def wait_for_dynamodb():
    """DynamoDB Local이 준비될 때까지 대기"""
    print("🔄 DynamoDB Local 연결 대기 중...")
    
    for attempt in range(30):  # 최대 30초 대기
        try:
            client = create_dynamodb_client()
            client.list_tables()
            print("✅ DynamoDB Local 연결 성공")
            return client
        except EndpointConnectionError:
            if attempt < 29:
                print(f"⏳ DynamoDB Local 대기 중... ({attempt + 1}/30)")
                time.sleep(1)
            else:
                print("❌ DynamoDB Local 연결 실패. Docker 컨테이너가 실행 중인지 확인해주세요.")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            sys.exit(1)


def create_tables_with_pynamodb():
    """PynamoDB 모델을 사용하여 테이블 생성"""
    created = 0
    exists = 0
    models = [Book, AudioChapter]

    for model in models:
        try:
            table_name = model.Meta.table_name
            if not model.exists():
                print(f"🛠️  PynamoDB로 테이블 생성: {table_name}")
                model.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
                print(f"🎉 {table_name} 생성 완료")
                created += 1
            else:
                print(f"ℹ️  {table_name} 이미 존재")
                exists += 1
        except Exception as e:
            print(f"❌ {model.__name__} 테이블 생성 실패: {e}")
            return False

    # 모든 모델이 생성되었거나 이미 존재하면 성공으로 간주
    return (created + exists) == len(models)


def create_sample_data_with_models():
    """샘플 데이터 생성 (PynamoDB 모델 사용)"""
    print("📝 샘플 데이터 생성 중(PynamoDB 모델 기반)...")

    # 샘플 Book
    try:
        book = Book(
            user_id="test_user",
            book_id="sample-book-001",
            title="샘플 오디오북",
            author="테스트 작가",
            publisher="테스트 출판사",
        )
        book.save()

        # 샘플 AudioChapter
        chapter = AudioChapter(
            chapter_id="sample-audio-001",
            book_id=book.book_id,
            chapter_number=1,
            title="챕터 1",
            file_info=FileInfo(
                original_name="0001.wav",
                file_size=32000,
                mime_type="audio/wav",
                local_path=f"storage/audio/book/{book.book_id}/media/0001.m4a",
            ),
            status="ready",
        )
        chapter.save()

        print("✅ 샘플 데이터 생성 완료")
        return True
    except Exception as e:
        print(f"⚠️  샘플 데이터 생성 실패: {e}")
        return False


def create_sample_data_legacy(client):
    """(레거시) boto3로 샘플 데이터 생성 - 유지용"""
    try:
        client.list_tables()
    except Exception:
        return False
    return True


def list_tables(client):
    """생성된 테이블 목록 출력"""
    try:
        response = client.list_tables()
        tables = response['TableNames']
        
        print("\n📋 생성된 테이블 목록:")
        for table in tables:
            print(f"  - {table}")
            
        return True
        
    except ClientError as e:
        print(f"❌ 테이블 목록 조회 실패: {e}")
        return False


def main():
    """메인 함수"""
    print("🚀 DynamoDB Local 테이블 생성 시작...")
    print("=" * 50)
    
    # DynamoDB Local 연결 대기
    client = wait_for_dynamodb()
    
    # 테이블 생성(PynamoDB)
    created_ok = create_tables_with_pynamodb()
    
    # 샘플 데이터 생성(PynamoDB)
    create_sample_data_with_models()
    
    # 결과 출력
    print("\n" + "=" * 50)
    if created_ok:
        print("🎉 모든 테이블 생성 완료!(PynamoDB)")
        list_tables(client)
        
        print("\n🔗 DynamoDB Admin UI: http://localhost:8002")
        print("💡 Admin UI에서 생성된 테이블과 샘플 데이터를 확인할 수 있습니다.")
        
    else:
        print("⚠️  일부 테이블 생성 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
