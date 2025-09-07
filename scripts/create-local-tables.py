#!/usr/bin/env python3
"""
DynamoDB Local 테이블 생성 스크립트

설계 문서의 데이터 모델을 기반으로 로컬 개발용 DynamoDB 테이블을 생성합니다.
"""

import boto3
import sys
import time
from botocore.exceptions import ClientError, EndpointConnectionError


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


def create_books_table(client):
    """Books 테이블 생성"""
    table_name = 'voj-books-local'
    
    try:
        response = client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'book_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'book_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand 모드
        )
        
        print(f"✅ {table_name} 테이블 생성 요청 완료")
        
        # 테이블이 활성화될 때까지 대기
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"🎉 {table_name} 테이블 생성 완료")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"ℹ️  {table_name} 테이블이 이미 존재합니다")
            return True
        else:
            print(f"❌ {table_name} 테이블 생성 실패: {e}")
            return False


def create_audio_chapters_table(client):
    """AudioChapters 테이블 생성"""
    table_name = 'voj-audio-chapters-local'
    
    try:
        response = client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'pk',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'sk',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'pk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'sk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'audio_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {
                            'AttributeName': 'audio_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand 모드
        )
        
        print(f"✅ {table_name} 테이블 생성 요청 완료")
        
        # 테이블이 활성화될 때까지 대기
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"🎉 {table_name} 테이블 생성 완료 (GSI 포함)")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"ℹ️  {table_name} 테이블이 이미 존재합니다")
            return True
        else:
            print(f"❌ {table_name} 테이블 생성 실패: {e}")
            return False


def create_sample_data(client):
    """샘플 데이터 생성 (개발용)"""
    print("📝 샘플 데이터 생성 중...")
    
    # Books 테이블에 샘플 책 데이터 추가
    try:
        client.put_item(
            TableName='voj-books-local',
            Item={
                'book_id': {'S': 'sample-book-001'},
                'title': {'S': '샘플 오디오북'},
                'author': {'S': '테스트 작가'},
                'publisher': {'S': '테스트 출판사'},
                'cover_key': {'S': 'book/sample-book-001/cover.jpg'},
                'created_at': {'S': '2024-01-01T00:00:00Z'},
                'updated_at': {'S': '2024-01-01T00:00:00Z'}
            }
        )
        
        # AudioChapters 테이블에 샘플 챕터 데이터 추가
        client.put_item(
            TableName='voj-audio-chapters-local',
            Item={
                'pk': {'S': 'book#sample-book-001'},
                'sk': {'S': 'order#0001'},
                'audio_id': {'S': 'sample-audio-001'},
                'file_key': {'S': 'book/sample-book-001/media/0001.m4a'},
                'source_key': {'S': 'book/sample-book-001/uploads/0001.wav'},
                'order': {'N': '1'},
                'duration_sec': {'N': '320'},
                'format': {'S': 'm4a'},
                'bitrate_kbps': {'N': '56'},
                'sample_rate': {'N': '44100'},
                'channels': {'N': '1'},
                'created_at': {'S': '2024-01-01T00:00:00Z'}
            }
        )
        
        print("✅ 샘플 데이터 생성 완료")
        return True
        
    except ClientError as e:
        print(f"⚠️  샘플 데이터 생성 실패: {e}")
        return False


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
    
    # 테이블 생성
    success_count = 0
    
    if create_books_table(client):
        success_count += 1
        
    if create_audio_chapters_table(client):
        success_count += 1
    
    # 샘플 데이터 생성
    create_sample_data(client)
    
    # 결과 출력
    print("\n" + "=" * 50)
    if success_count == 2:
        print("🎉 모든 테이블 생성 완료!")
        list_tables(client)
        
        print("\n🔗 DynamoDB Admin UI: http://localhost:8002")
        print("💡 Admin UI에서 생성된 테이블과 샘플 데이터를 확인할 수 있습니다.")
        
    else:
        print(f"⚠️  일부 테이블 생성 실패 ({success_count}/2)")
        sys.exit(1)


if __name__ == "__main__":
    main()
