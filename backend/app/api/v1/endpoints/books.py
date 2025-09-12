"""
VOJ Audiobooks API - 책 관리 엔드포인트
책 생성, 조회, 수정, 삭제 기능
"""
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.config import settings

router = APIRouter()


class BookBase(BaseModel):
    """책 기본 정보 모델"""
    title: str = Field(..., min_length=1, max_length=200, description="책 제목")
    author: str = Field(..., min_length=1, max_length=100, description="저자")
    description: Optional[str] = Field(None, max_length=1000, description="책 설명")
    genre: Optional[str] = Field(None, max_length=50, description="장르")
    language: str = Field(default="ko", description="언어 코드")
    isbn: Optional[str] = Field(None, description="ISBN")
    publisher: Optional[str] = Field(None, max_length=100, description="출판사")
    published_date: Optional[datetime] = Field(None, description="출간일")


class BookCreate(BookBase):
    """책 생성 요청 모델"""
    pass


class BookUpdate(BaseModel):
    """책 수정 요청 모델"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    genre: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = Field(None, max_length=100)
    published_date: Optional[datetime] = None


class Book(BookBase):
    """책 응답 모델"""
    book_id: str
    user_id: str
    status: str = Field(default="draft", description="상태: draft, processing, published, error")
    created_at: datetime
    updated_at: datetime
    total_chapters: int = Field(default=0, description="총 챕터 수")
    total_duration: int = Field(default=0, description="총 재생 시간(초)")
    cover_image_url: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookList(BaseModel):
    """책 목록 응답 모델"""
    books: List[Book]
    total: int
    page: int
    size: int
    has_next: bool


@router.post("/", response_model=Book, status_code=201)
async def create_book(book_data: BookCreate):
    """
    새 책 생성
    - 사용자 인증 필요
    - DynamoDB에 책 정보 저장
    """
    # TODO: 사용자 인증 확인
    # TODO: DynamoDB에 책 정보 저장
    
    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        book_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        return Book(
            book_id=book_id,
            user_id="dummy_user_id",
            title=book_data.title,
            author=book_data.author,
            description=book_data.description,
            genre=book_data.genre,
            language=book_data.language,
            isbn=book_data.isbn,
            publisher=book_data.publisher,
            published_date=book_data.published_date,
            status="draft",
            created_at=now,
            updated_at=now,
            total_chapters=0,
            total_duration=0
        )
    
    raise HTTPException(
        status_code=501,
        detail="Book creation not implemented yet"
    )


@router.get("/", response_model=BookList)
async def get_books(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    status: Optional[str] = Query(None, description="책 상태 필터"),
    genre: Optional[str] = Query(None, description="장르 필터"),
    search: Optional[str] = Query(None, description="제목/저자 검색")
):
    """
    책 목록 조회
    - 페이징 지원
    - 상태, 장르, 검색어로 필터링
    - 사용자별 책만 조회
    """
    # TODO: 사용자 인증 확인
    # TODO: DynamoDB에서 책 목록 조회
    
    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        now = datetime.utcnow()
        dummy_books = [
            Book(
                book_id=f"book_{i}",
                user_id="dummy_user_id",
                title=f"테스트 책 {i}",
                author=f"저자 {i}",
                description=f"테스트 책 {i}의 설명입니다.",
                genre="fiction",
                language="ko",
                status="draft",
                created_at=now,
                updated_at=now,
                total_chapters=0,
                total_duration=0
            )
            for i in range(1, 6)
        ]
        
        return BookList(
            books=dummy_books[:size],
            total=len(dummy_books),
            page=page,
            size=size,
            has_next=len(dummy_books) > page * size
        )
    
    raise HTTPException(
        status_code=501,
        detail="Book listing not implemented yet"
    )


@router.get("/{book_id}", response_model=Book)
async def get_book(
    book_id: str = Path(..., description="책 ID")
):
    """
    특정 책 상세 조회
    - 사용자 인증 필요
    - 본인의 책만 조회 가능
    """
    # TODO: 사용자 인증 확인
    # TODO: 책 소유권 확인
    # TODO: DynamoDB에서 책 정보 조회
    
    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        now = datetime.utcnow()
        return Book(
            book_id=book_id,
            user_id="dummy_user_id",
            title="테스트 책",
            author="테스트 저자",
            description="테스트 책의 상세 설명입니다.",
            genre="fiction",
            language="ko",
            status="draft",
            created_at=now,
            updated_at=now,
            total_chapters=0,
            total_duration=0
        )
    
    raise HTTPException(
        status_code=404,
        detail="Book not found"
    )


@router.put("/{book_id}", response_model=Book)
async def update_book(
    book_data: BookUpdate,
    book_id: str = Path(..., description="책 ID")
):
    """
    책 정보 수정
    - 사용자 인증 필요
    - 본인의 책만 수정 가능
    """
    # TODO: 사용자 인증 확인
    # TODO: 책 소유권 확인
    # TODO: DynamoDB에서 책 정보 수정
    
    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        now = datetime.utcnow()
        return Book(
            book_id=book_id,
            user_id="dummy_user_id",
            title=book_data.title or "수정된 테스트 책",
            author=book_data.author or "수정된 저자",
            description=book_data.description,
            genre=book_data.genre,
            language=book_data.language or "ko",
            isbn=book_data.isbn,
            publisher=book_data.publisher,
            published_date=book_data.published_date,
            status="draft",
            created_at=now,
            updated_at=now,
            total_chapters=0,
            total_duration=0
        )
    
    raise HTTPException(
        status_code=404,
        detail="Book not found"
    )


@router.delete("/{book_id}")
async def delete_book(
    book_id: str = Path(..., description="책 ID")
):
    """
    책 삭제
    - 사용자 인증 필요
    - 본인의 책만 삭제 가능
    - 연관된 오디오 파일도 함께 삭제
    """
    # TODO: 사용자 인증 확인
    # TODO: 책 소유권 확인
    # TODO: 연관된 오디오 챕터 삭제
    # TODO: S3/로컬 스토리지에서 파일 삭제
    # TODO: DynamoDB에서 책 정보 삭제
    
    if settings.ENVIRONMENT == "local":
        return {"message": f"Book {book_id} deleted successfully (local dev mode)"}
    
    raise HTTPException(
        status_code=404,
        detail="Book not found"
    )

