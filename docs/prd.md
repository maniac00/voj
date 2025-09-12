# 📄 PRD: 시각장애인용 오디오북 스트리밍 MVP (웹 어드민)

## 1. 목적

* 시각장애인을 위한 오디오북 서비스 MVP를 구축한다.
* 관리자는 AWS 기반 웹 어드민에서 책과 오디오 파일을 등록/관리할 수 있다.
* 사용자는 모바일 앱(또는 웹 플레이어)에서 스트리밍 방식으로 오디오북을 청취할 수 있다.
* MVP 단계에서는 기본적인 **책 메타데이터 관리 + 오디오 파일 업로드/순서 관리 + 스트리밍 준비**까지 포함한다.

---

## 2. 주요 사용자

1. **관리자(Admin)**:

   * 웹 어드민에서 책과 오디오 파일을 등록/편집/삭제
   * 오디오 순서를 지정
   * 표지 이미지 업로드
2. **사용자(User, 시각장애인 최종 이용자)**:

   * 앱에서 책 리스트와 챕터(오디오 파일) 리스트 확인
   * 오디오 스트리밍 청취 (다운로드 방지)

---

## 3. 주요 기능 정의

### 3.1 책(Book) 관리

* **필드**

  * 제목 (title)
  * 저자 (author)
  * 출판사 (publisher)
  * 표지 이미지 (cover\_image)
* **기능**

  * 책 등록(Create)
  * 책 수정(Update)
  * 책 삭제(Delete)
  * 책 목록 조회(Read, pagination 포함)

### 3.2 오디오 파일(Audio/Chapter) 관리

* **필드**

  * 파일명 (auto)
  * 순서(order)
  * 파일 경로(S3 URL, presigned URL 기반 접근)
  * 재생 시간(duration, ffmpeg 메타데이터 추출)
* **기능**

  * 오디오 파일 업로드 (S3 비공개 버킷에 저장)
  * 업로드 후 자동 인코딩(예: WAV → AAC/Opus)
  * 책에 소속된 오디오 리스트 관리
  * 오디오 순서 변경 (drag & drop 또는 order 필드 수정)
  * 오디오 삭제

### 3.3 스트리밍 지원

* 오디오 파일은 **S3 비공개 저장** 후 **CloudFront Signed URL**로 제공
* Range 요청 허용 (프로그레시브 스트리밍)
* 향후 HLS 변환(세그먼트화) 확장 가능하도록 준비

### 3.4 권한 및 보안

* 어드민 로그인 (최소 email/password, Cognito 권장)
* 모든 S3 오브젝트는 public 불가 → presigned URL 또는 CloudFront Signed URL로만 접근
* 업로드 시 서버에서 **ffmpeg 인코딩 워커** 실행 (Lambda or ECS Fargate)

---

## 4. 기술 아키텍처 (MVP 버전)

* **프론트엔드(웹 어드민):** React/Next.js (간단 UI)
* **백엔드 API:** AWS API Gateway + Lambda (Python/FastAPI)
* **DB:** DynamoDB (Book/Audio 메타데이터 저장)
* **스토리지:** S3 (오디오/이미지 저장, 비공개)
* **CDN:** CloudFront (보안 스트리밍 배포)
* **인증:** AWS Cognito (어드민 로그인 + 토큰 기반)
* **인코딩 파이프라인:** S3 업로드 → S3 이벤트 → Lambda(ffmpeg) → 결과 저장

---

## 5. 데이터 모델 (초안)

**Book**

```json
{
  "book_id": "uuid",
  "title": "string",
  "author": "string",
  "publisher": "string",
  "cover_image_url": "s3://bucket/book123/cover.jpg",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

**Audio**

```json
{
  "audio_id": "uuid",
  "book_id": "uuid",
  "order": 1,
  "file_url": "s3://bucket/book123/audio001.m4a",
  "duration": 320, 
  "created_at": "timestamp"
}
```

---

## 6. MVP 범위 (In / Out)

✅ **In Scope**

* 책 CRUD
* 오디오 파일 업로드/순서 지정
* S3 업로드 및 CloudFront 스트리밍
* 어드민 로그인
* ffmpeg 인코딩 자동화 (단일 비트레이트)

❌ **Out of Scope (향후 확장)**

* HLS 멀티비트레이트 스트리밍
* 모바일 앱 완전 개발(현재는 테스트용 웹 플레이어 정도)
* 결제/회원관리
* 음성 검색/자막 지원
* 추천/북마크/통계

---

## 7. 향후 확장 고려

* HLS/AES-128 암호화 적용
* 오프라인 캐시(앱 내 저장, 만료기간)
* 다국어/다형식 지원 (Opus, AAC, MP3 자동 변환)
* 챕터별 텍스트 동기화 (스크립트 자막 제공)

---

👉 요약:
이 MVP는 **책과 오디오 관리 + 순서 지정 + 스트리밍 가능 상태**를 목표로 하고, **AWS S3 + CloudFront + DynamoDB + Lambda(ffmpeg)** 조합으로 빠르게 만들 수 있습니다.
