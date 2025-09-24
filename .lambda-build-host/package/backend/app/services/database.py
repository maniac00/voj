"""
VOJ Audiobooks API - 데이터베이스 서비스
DynamoDB 연결 및 테이블 관리
"""
import asyncio
from typing import List, Optional
from pynamodb.exceptions import TableError, DoesNotExist

from app.core.config import settings
from app.models.book import Book
from app.models.audio_chapter import AudioChapter


class DatabaseService:
    """데이터베이스 연결 및 관리 서비스"""
    
    def __init__(self):
        self.models = [Book, AudioChapter]
        self._connection_tested = False
    
    async def test_connection(self) -> bool:
        """DynamoDB 연결 테스트"""
        try:
            # 각 모델의 테이블 존재 여부 확인
            for model in self.models:
                model.exists()
            
            self._connection_tested = True
            return True
        except Exception as e:
            print(f"DynamoDB connection test failed: {e}")
            return False
    
    async def create_tables_if_not_exist(self) -> dict:
        """테이블이 존재하지 않으면 생성"""
        results = {}
        
        for model in self.models:
            try:
                table_name = model.Meta.table_name
                
                if not model.exists():
                    print(f"Creating table: {table_name}")
                    
                    # 테이블 생성 옵션
                    create_options = {
                        'read_capacity_units': 5,
                        'write_capacity_units': 5,
                        'wait': True  # 테이블 생성 완료까지 대기
                    }
                    
                    model.create_table(**create_options)
                    results[table_name] = "created"
                    print(f"Table {table_name} created successfully")
                else:
                    results[table_name] = "exists"
                    print(f"Table {table_name} already exists")
                    
            except Exception as e:
                results[model.Meta.table_name] = f"error: {str(e)}"
                print(f"Error with table {model.Meta.table_name}: {e}")
        
        return results
    
    async def get_table_status(self) -> dict:
        """테이블 상태 조회"""
        status = {}
        
        for model in self.models:
            table_name = model.Meta.table_name
            try:
                if model.exists():
                    # 테이블 메타데이터 조회
                    table_meta = model.describe_table()
                    status[table_name] = {
                        "status": "active",
                        "item_count": table_meta.get('ItemCount', 0),
                        "table_size": table_meta.get('TableSizeBytes', 0),
                    }
                else:
                    status[table_name] = {"status": "not_found"}
            except Exception as e:
                status[table_name] = {"status": "error", "error": str(e)}
        
        return status
    
    async def health_check(self) -> dict:
        """데이터베이스 헬스 체크"""
        health_status = {
            "status": "healthy",
            "connection": False,
            "tables": {},
            "environment": settings.ENVIRONMENT
        }
        
        try:
            # 연결 테스트
            health_status["connection"] = await self.test_connection()
            
            # 테이블 상태 확인
            health_status["tables"] = await self.get_table_status()
            
            # 전체 상태 결정
            if not health_status["connection"]:
                health_status["status"] = "unhealthy"
            elif any(table.get("status") == "error" for table in health_status["tables"].values()):
                health_status["status"] = "degraded"
        
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def initialize(self) -> dict:
        """데이터베이스 초기화"""
        print("Initializing database...")
        
        # 연결 테스트
        connection_ok = await self.test_connection()
        if not connection_ok:
            raise Exception("Failed to connect to DynamoDB")
        
        # 테이블 생성
        table_results = await self.create_tables_if_not_exist()
        
        print("Database initialization completed")
        return {
            "connection": connection_ok,
            "tables": table_results
        }


# 전역 데이터베이스 서비스 인스턴스
db_service = DatabaseService()

