"""
VOJ Audiobooks API - DynamoDB 기본 모델
PynamoDB를 사용한 DynamoDB 모델 기본 클래스
"""
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
from datetime import datetime
from typing import Optional

from app.core.config import settings


class BaseModel(Model):
    """DynamoDB 모델 기본 클래스"""
    
    class Meta:
        region = settings.AWS_REGION
        
        # 환경별 엔드포인트 설정
        if settings.ENVIRONMENT == "local" and settings.DYNAMODB_ENDPOINT_URL:
            host = settings.DYNAMODB_ENDPOINT_URL
            # DynamoDB Local용 더미 자격증명
            aws_access_key_id = "dummy"
            aws_secret_access_key = "dummy"
    
    # 공통 속성
    created_at = UTCDateTimeAttribute(default=datetime.utcnow)
    updated_at = UTCDateTimeAttribute(default=datetime.utcnow)
    
    def save(self, **kwargs):
        """저장 시 updated_at 자동 업데이트"""
        self.updated_at = datetime.utcnow()
        return super().save(**kwargs)
    
    def update(self, actions, **kwargs):
        """업데이트 시 updated_at 자동 업데이트"""
        from pynamodb.expressions.update import Set
        
        # updated_at 업데이트 액션 추가
        if not any(isinstance(action, Set) and action.path[0] == 'updated_at' for action in actions):
            actions.append(Set(self.updated_at, datetime.utcnow()))
        
        return super().update(actions, **kwargs)
    
    @classmethod
    def create_table_if_not_exists(cls, **kwargs):
        """테이블이 존재하지 않으면 생성"""
        try:
            if not cls.exists():
                cls.create_table(**kwargs)
                return True
            return False
        except Exception as e:
            print(f"Error creating table {cls.Meta.table_name}: {e}")
            return False

