"""
VOJ Audiobooks API - 데이터베이스 서비스
SQLAlchemy 기반 데이터베이스 헬스체크 및 초기화
"""
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.models.audio_chapter_sql import AudioChapterSQL
from app.models.book_sql import BookSQL
from app.models.database import Base, SessionLocal, engine


class DatabaseService:
    """데이터베이스 연결 및 관리 서비스 (PostgreSQL/SQLite)"""

    async def test_connection(self) -> bool:
        """DB 연결 테스트 (SELECT 1)"""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    async def get_table_status(self) -> dict:
        """중요 테이블 존재 여부 및 간단한 카운트 조회"""
        status: dict = {}
        inspector = inspect(engine)
        with SessionLocal() as db:
            for table_name, model in (
                ("books", BookSQL),
                ("audio_chapters", AudioChapterSQL),
            ):
                try:
                    if not inspector.has_table(table_name):
                        status[table_name] = {"status": "not_found"}
                        continue
                    count = db.query(model).count()
                    status[table_name] = {"status": "active", "row_count": count}
                except SQLAlchemyError as e:
                    status[table_name] = {"status": "error", "error": str(e)}
                except Exception as e:
                    status[table_name] = {"status": "error", "error": str(e)}
        return status

    async def health_check(self) -> dict:
        """데이터베이스 헬스 체크"""
        health_status = {
            "status": "healthy",
            "connection": False,
            "tables": {},
            "environment": settings.ENVIRONMENT,
            "dialect": engine.url.get_backend_name(),
        }

        try:
            health_status["connection"] = await self.test_connection()
            health_status["tables"] = await self.get_table_status()

            if not health_status["connection"]:
                health_status["status"] = "unhealthy"
            elif any(
                t.get("status") == "error" for t in health_status["tables"].values()
            ):
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    async def initialize(self) -> dict:
        """로컬 초기화: SQL 테이블 생성 (마이그레이션 대용)"""
        try:
            Base.metadata.create_all(bind=engine)
            return {"created": True}
        except Exception as e:
            raise Exception(f"Failed to initialize SQL tables: {e}")


# 전역 데이터베이스 서비스 인스턴스
db_service = DatabaseService()
