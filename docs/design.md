# 시각장애인용 오디오북 MVP – 설계 문서

## 0. 목표와 범위

* **목표:** 책(메타데이터)과 오디오(여러 개, 순서 지정)를 등록·관리하고, 앱/웹에서 **권리보호형 스트리밍**으로 재생.
* **범위(MVP):**

  * 웹 어드민: 책/오디오 CRUD, 오디오 업로드, 순서 변경
  * 음원 처리: **WAV → AAC(m4a) 1종 변환**, 재생시간/메타 추출
  * 배포: **CloudFront(OAC) + S3 비공개** + **Signed URL**
  * 인증: **어드민용 Cognito**
* **비범위(차기):** HLS 멀티비트레이트, 결제/회원, 앱 오프라인 캐시, 자막 동기화

---

## 1. 아키텍처 개요

* **프론트(어드민)**: Next.js (App Router)
* **백엔드 API**: API Gateway + Lambda(FastAPI or Lambda Powertools)
* **DB**: DynamoDB (Books/AudioChapters)
* **스토리지**: S3 (비공개 버킷, 서울 `ap-northeast-2`)
* **CDN/보안**: CloudFront + Origin Access Control(OAC) + Signed URL/쿠키
* **인증/권한**: Cognito(어드민), IAM(OAC, Lambda 역할 최소권한)
* **인코딩 워크플로우**: S3 Put("uploads/") → S3 Event → Lambda(FFmpeg) → "media/"에 결과 저장 → 메타 업데이트

## 1.1 개발 환경 구성

### 로컬 개발 환경 (MacBook)

* **프론트엔드**: Next.js 개발 서버 (`localhost:3000`)
* **백엔드**: FastAPI 로컬 서버 (`localhost:8000`)
* **DB**: DynamoDB Local (Docker 또는 Java 기반)
* **스토리지**: 로컬 파일 시스템 (`./storage/audio/`)
* **인증**: Mock 인증 또는 로컬 JWT
* **인코딩**: 로컬 FFmpeg 바이너리

**특징:**
- 프로젝트 폴더 복사만으로 동일한 개발 환경 구성 가능
- 설치 스크립트 (`scripts/setup-local.sh`) 제공
- 오디오 파일은 `./storage/audio/book/{book_id}/` 구조로 저장
- 환경 변수로 로컬/프로덕션 모드 구분

### 프로덕션 환경 (AWS)

* **프론트엔드**: Vercel 또는 AWS Amplify
* **백엔드**: API Gateway + Lambda
* **DB**: DynamoDB (서울 리전)
* **스토리지**: S3 (비공개 버킷)
* **CDN**: CloudFront + OAC
* **인증**: AWS Cognito
* **인코딩**: Lambda + FFmpeg Layer

**특징:**
- IaC 기반 배포 (CDK 또는 Terraform)
- 배포 스크립트 (`scripts/deploy-prod.sh`) 제공
- 자동 스케일링 및 모니터링
- 앱에서 CloudFront Signed URL로 스트리밍

### 요청 흐름(핵심)

1. 어드민 로그인(Cognito)
2. 책 생성(메타만) → 표지 업로드(직접 S3 프리사인드 Put)
3. **오디오 업로드**(WAV → `uploads/…`)
4. S3 Event → **Encode Lambda**(WAV→AAC m4a, 메타 추출) → `media/…` 저장
5. 백엔드가 Audio 레코드 생성/업데이트(파일 경로, duration 등)
6. 앱/웹 플레이어 요청 시 **API가 CloudFront Signed URL** 발급 → 재생(HTTP Range 허용)

---

## 2. 데이터 모델

### DynamoDB – Books (파티션 키: `book_id`)

```json
{
  "book_id": "uuid",
  "title": "string",
  "author": "string",
  "publisher": "string",
  "cover_key": "book/{book_id}/cover.jpg",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### DynamoDB – AudioChapters (복합키: PK=`book#{book_id}`, SK=`order#{0001}`)

```json
{
  "pk": "book#<book_id>",
  "sk": "order#0001",
  "audio_id": "uuid",
  "file_key": "book/<book_id>/media/0001.m4a",
  "source_key": "book/<book_id>/uploads/0001.wav",
  "order": 1,
  "duration_sec": 320,
  "format": "m4a",
  "bitrate_kbps": 56,
  "sample_rate": 44100,
  "channels": 1,
  "created_at": "ISO8601"
}
```

* **정렬**은 `order` 기반(앞 4자리 zero-padding)
* **GSI(Optional)**: `GSI1PK = audio_id`, `GSI1SK = created_at` (단건 조회/진단)

---

## 3. 스토리지 구조 & 네이밍

### 3.1 로컬 개발 환경

```
./storage/
  audio/
    book/<book_id>/
      cover/cover.jpg
      uploads/0001.wav        # 원본 업로드
      media/0001.m4a          # 인코딩 결과
```

### 3.2 프로덕션 환경 (S3)

```
s3://<bucket>/
  book/<book_id>/
    cover/cover.jpg
    uploads/0001.wav          # 원본 업로드(비공개)
    media/0001.m4a            # 인코딩 결과(비공개, CloudFront로만 접근)
```

**버킷 설정**

* Block Public Access = **ON**
* Default Encryption = **SSE-S3**(또는 KMS)
* CORS(필요 최소): PUT(업로드), GET(커버 미리보기 시), HEAD, Range

예) CORS 간단 예시(어드민 도메인 한정):

```xml
<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>https://admin.example.com</AllowedOrigin>
    <AllowedMethod>PUT</AllowedMethod>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedMethod>HEAD</AllowedMethod>
    <AllowedHeader>*</AllowedHeader>
    <ExposeHeader>ETag</ExposeHeader>
  </CORSRule>
</CORSConfiguration>
```

---

## 4. CloudFront 구성(권리보호)

* **Origin**: S3(비공개) + **OAC**로 원본 접근 제한
* **Behavior**:

  * Cache Policy: Range 헤더 허용(프로그레시브 스트리밍)
  * Response Headers Policy: CORS 최소 허용(앱/웹 도메인만)
* **보안 접근**: **Signed URL(or Cookie)**, TTL 짧게(예: 60\~120초)
* **다운로드 억제**: 완전 차단 불가. 다만 \*\*짧은 만료 + 도메인 고정 + 세그먼트화(HLS로 확장 예정)\*\*로 억제

---

## 5. 인코딩 파이프라인(FFmpeg)

### 트리거

* S3 PUT(`book/<id>/uploads/*.wav`) → EventBridge or S3 Event → **Encode Lambda**

### FFmpeg 프리셋(MVP 단일)

* **코덱**: AAC-LC (m4a 컨테이너)
* **채널**: 모노(`-ac 1`)
* **샘플레이트**: 44.1kHz(`-ar 44100`)
* **비트레이트**: 56 kbps(`-b:a 56k`)
* **faststart**: `-movflags +faststart` (초기 재생 개선)

#### 명령 샘플

```bash
ffmpeg -i input.wav -ac 1 -ar 44100 -c:a aac -b:a 56k -movflags +faststart output.m4a
```

### 메타데이터 추출

* `ffprobe -v quiet -print_format json -show_format -show_streams output.m4a`

  * duration, sample\_rate, channels, bitrate 추출 → DynamoDB 업데이트

### Lambda 구현 요점

* **런타임**: Python 3.12
* **FFmpeg 배포**: Lambda Layer(정적 빌드), `/opt/ffmpeg` 사용
* **IAM 최소권한**:

  * S3\:GetObject(`uploads/*`), S3\:PutObject(`media/*`), DynamoDB\:UpdateItem
* **타임아웃**: 파일 길이에 따라 30\~120초(장편은 분할 업로드 권장)
* **리트라이**: DLQ(SQS) 연결, 장애 시 재처리

---

## 6. API 설계(요약)

### 인증

* **Cognito Admin Pool**: 이메일/비밀번호 로그인 → ID Token/JWT
* API Gateway: Cognito Authorizer

### 엔드포인트(예시)

* `POST /books` – 책 생성
* `GET /books?cursor=` – 책 페이지 조회
* `GET /books/{book_id}` – 단건 조회
* `PUT /books/{book_id}` – 수정
* `DELETE /books/{book_id}` – 삭제
* `POST /books/{book_id}/cover:presign` – 표지 업로드용 **프리사인드 PUT** 발급
* `POST /books/{book_id}/audios:presign` – WAV 업로드용 **프리사인드 PUT** 발급(키 반환)
* `GET /books/{book_id}/audios` – 챕터 목록(정렬: order)
* `PUT /books/{book_id}/audios/{audio_id}` – 메타/순서 수정
* `DELETE /books/{book_id}/audios/{audio_id}` – 삭제
* `POST /stream/{audio_id}:sign` – **CloudFront Signed URL** 생성(짧은 만료)

#### `POST /stream/{audio_id}:sign` 응답 예

```json
{
  "url": "https://dxxxxx.cloudfront.net/book/<book_id>/media/0001.m4a?Expires=...&Signature=...&Key-Pair-Id=..."
}
```

---

## 7. 어드민 UX 요건(접근성 친화)

* 폼 필드: 제목/저자/출판사/표지 업로드
* 오디오 관리: **드래그앤드롭 업로드(WAV)** → 업로드 큐/상태(대기/인코딩/완료/오류)
* 순서 변경: 드래그 정렬 → 일괄 저장
* 챕터 미리듣기: CloudFront Signed URL로 10\~20초 샘플 재생
* 키보드 내비게이션, 큰 버튼, 포커스 링 강조(시각장애 보조 관리자 고려)

---

## 8. 보안 & 권리보호

* **S3 비공개**, **CloudFront OAC**
* **Signed URL TTL 짧게**(60\~120초) + 1회 요청마다 재발급
* **Range GET 허용**(재생 위치 이동)
* **쿠키/도메인 바인딩**(웹일 경우)
* **서버 사이드 로그**(CloudFront/S3 Access Logs, API Gateway 로그)
* **동시 스트림 제한(선택)**: 계정별 동시 재생 수 카운트(레디스/디나모 토큰)로 억제
* **워터마킹(차기)**: HLS 도입 시 세그먼트 워터마크 옵션 검토

### 8.1 시크릿 관리 원칙

- 코드 내 시크릿(예: `LocalSettings`의 Cognito Client Secret) 하드코딩 금지
- 로컬: `.env.local` 사용(값 비워두면 인증 BYPASS로 개발 편의 유지)
- 프로덕션: AWS Secrets Manager 또는 Parameter Store 사용, 주기적 롤테이션
- 헬스체크에 Cognito 환경 변수 누락 경고 추가(로컬=warning, 프로덕션=unhealthy)

---

## 9. 관측/운영

* **지표**: 인코딩 성공률, 평균 인코딩 시간, 4xx/5xx 비율, 재생 시작 지연(TTFB), Range 요청 분포
* **알람**:

  * Lambda 오류율/재시도 초과
  * CloudFront 5xx 비율 상승
  * S3 403 비율 상승
* **로깅**: CloudFront(Standard logs), S3 Access, CloudWatch Logs(구조화)

---

## 10. 비용 대략(50 동시접속 가정)

* **S3 저장/전송**: 음원 용량 감소(AAC 56 kbps 기준: 약 25MB/h)로 저렴
* **CloudFront**: 한국 트래픽 단가 고려(캐시 히트↑로 비용↓)
* **Lambda**: 인코딩 시에만 비용 발생(트래픽 비례 아님)
* **DynamoDB/ApiGW/Cognito**: 저부하 구간 소액

> WAV → AAC 변환으로 **저장/전송 비용이 크게 절감**됩니다(수십 배).

---

## 11. 배포/권한(IaC 개요)

* IaC: CDK/Terraform(권장), 스택 분리: `network` / `data` / `app`
* **IAM 최소 권한 예(요지)**

  * Encode Lambda:

    * `s3:GetObject` on `book/*/uploads/*`
    * `s3:PutObject` on `book/*/media/*`
    * `dynamodb:UpdateItem` on `AudioChapters`
  * API Lambda: `dynamodb:*Item` on 두 테이블, `cloudfront:CreateInvalidation`(선택), `cloudfront:Sign*`(키 관리 방식에 따라 불필요할 수 있음)

---

## 12. 환경별 설정 및 스크립트

### 12.1 로컬 개발 환경 설정

#### 환경 변수 (.env.local)
```bash
# 개발 환경 구분
NODE_ENV=development
ENVIRONMENT=local

# 로컬 서버 설정
NEXT_PUBLIC_API_URL=http://localhost:8000
API_PORT=8000

# 로컬 DynamoDB
DYNAMODB_ENDPOINT=http://localhost:8001
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=local
AWS_SECRET_ACCESS_KEY=local

# 로컬 스토리지
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage/audio
LOCAL_STORAGE_BASE_URL=http://localhost:8000/storage

# FFmpeg 경로
FFMPEG_PATH=/opt/homebrew/bin/ffmpeg
FFPROBE_PATH=/opt/homebrew/bin/ffprobe
```

#### 설치 스크립트 (scripts/setup-local.sh)
```bash
#!/bin/bash
set -e

echo "🚀 로컬 개발 환경 설정 시작..."

# 1. 의존성 확인 및 설치
echo "📦 의존성 설치 중..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js가 설치되지 않았습니다. Node.js 18+ 설치 후 다시 실행해주세요."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되지 않았습니다."
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "🎵 FFmpeg 설치 중..."
    brew install ffmpeg
fi

# 2. Python 가상환경 설정
echo "🐍 Python 가상환경 설정 중..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Node.js 의존성 설치
echo "📦 Node.js 패키지 설치 중..."
npm install

# 4. 로컬 스토리지 디렉토리 생성
echo "📁 로컬 스토리지 디렉토리 생성 중..."
mkdir -p storage/audio

# 5. DynamoDB Local 설정
echo "🗄️ DynamoDB Local 설정 중..."
docker-compose up -d dynamodb-local

# 6. 환경 변수 파일 생성
if [ ! -f .env.local ]; then
    echo "⚙️ 환경 변수 파일 생성 중..."
    cp .env.local.example .env.local
fi

# 7. DynamoDB 테이블 생성
echo "🏗️ DynamoDB 테이블 생성 중..."
python scripts/create-local-tables.py

echo "✅ 로컬 개발 환경 설정 완료!"
echo "📝 다음 명령어로 개발 서버를 시작하세요:"
echo "   npm run dev:local"
```

### 12.2 프로덕션 환경 설정

#### 환경 변수 (.env.production)
```bash
# 프로덕션 환경 구분
NODE_ENV=production
ENVIRONMENT=production

# AWS 설정
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=voj-audiobook-prod
CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC
CLOUDFRONT_DOMAIN=d1234567890abc.cloudfront.net

# DynamoDB 테이블
DYNAMODB_BOOKS_TABLE=voj-books-prod
DYNAMODB_AUDIO_TABLE=voj-audio-chapters-prod

# Cognito 설정
COGNITO_USER_POOL_ID=ap-northeast-2_abcd1234
COGNITO_CLIENT_ID=1234567890abcdefghij

# API Gateway
API_GATEWAY_URL=https://api.voj-audiobook.com

# CloudFront 키 페어 (Signed URL용)
CLOUDFRONT_KEY_PAIR_ID=K1234567890ABC
CLOUDFRONT_PRIVATE_KEY_PATH=/opt/cloudfront-private-key.pem
```

#### 배포 스크립트 (scripts/deploy-prod.sh)
```bash
#!/bin/bash
set -e

echo "🚀 프로덕션 배포 시작..."

# 1. 환경 확인
if [ ! -f .env.production ]; then
    echo "❌ .env.production 파일이 없습니다."
    exit 1
fi

# 2. AWS CLI 설정 확인
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI가 설정되지 않았습니다."
    exit 1
fi

# 3. 프론트엔드 빌드
echo "🏗️ 프론트엔드 빌드 중..."
npm run build

# 4. 백엔드 패키징
echo "📦 백엔드 Lambda 패키징 중..."
cd backend
pip install -r requirements.txt -t ./package
cp -r src/* ./package/
cd ../

# 5. IaC 배포 (CDK)
echo "☁️ AWS 인프라 배포 중..."
cd infrastructure
npm install
npx cdk deploy --all --require-approval never
cd ../

# 6. 프론트엔드 배포 (Vercel 또는 S3)
echo "🌐 프론트엔드 배포 중..."
if [ "$FRONTEND_DEPLOY_TARGET" = "vercel" ]; then
    vercel --prod
else
    aws s3 sync ./out s3://$FRONTEND_S3_BUCKET --delete
    aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
fi

echo "✅ 프로덕션 배포 완료!"
```

### 12.3 개발 체크리스트

> 📋 **상세한 개발 체크리스트는 [`docs/checklist.md`](./checklist.md) 파일을 참조하세요.**
> 
> 체크리스트에는 다음 내용이 포함되어 있습니다:
> - 워크플로우 기반 계층화된 작업 목록 (1.1.1 형식)
> - 환경별 설정 가이드 (로컬/프로덕션)
> - 마일스톤 및 진행률 추적
> - 각 단계별 상세 구현 가이드

---

## 13. 간단 코드 스니펫(핵심 부분)

### (A) 업로드용 프리사인드 URL 발급(Python, boto3)

```python
import boto3, uuid, datetime as dt

s3 = boto3.client("s3")
def presign_upload(book_id: str, ext: str = "wav"):
    key = f"book/{book_id}/uploads/{uuid.uuid4().hex}.{ext}"
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": BUCKET, "Key": key, "ContentType": "audio/wav"},
        ExpiresIn=300  # 5분
    )
    return {"key": key, "url": url}
```

### (B) 인코딩 Lambda(핵심 호출부)

```python
import subprocess, json, os
def run_ffmpeg(in_path, out_path):
    cmd = ["/opt/ffmpeg/ffmpeg", "-y",
           "-i", in_path, "-ac", "1", "-ar", "44100",
           "-c:a", "aac", "-b:a", "56k", "-movflags", "+faststart", out_path]
    subprocess.check_call(cmd)

def probe(path):
    out = subprocess.check_output(
        ["/opt/ffmpeg/ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", path]
    )
    return json.loads(out)
```

### (C) CloudFront Signed URL 발급(개념)

* 키 쌍 생성 후, 백엔드에서 Policy/Signature 생성 → 짧은 만료로 URL 반환
* 라이브러리는 언어별(예: Node `@aws-sdk/cloudfront-signer`) 사용

---

## 14. 앱 스트리밍 고려사항

### 14.1 환경별 스트리밍 URL 처리

#### 로컬 개발 환경
```javascript
// 로컬에서는 직접 파일 서빙
const getAudioUrl = (audioId) => {
  if (process.env.ENVIRONMENT === 'local') {
    return `${process.env.LOCAL_STORAGE_BASE_URL}/book/${bookId}/media/${audioId}.m4a`;
  }
  // 프로덕션에서는 Signed URL 요청
  return await fetch(`/api/stream/${audioId}/sign`).then(res => res.json());
};
```

#### 프로덕션 환경
```javascript
// CloudFront Signed URL 사용
const getSignedUrl = async (audioId) => {
  const response = await fetch(`/api/stream/${audioId}/sign`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { url } = await response.json();
  return url; // 60-120초 TTL
};
```

### 14.2 앱에서의 스트리밍 최적화

#### Progressive Download 지원
- **Range 요청**: 앱에서 특정 구간 재생 시 필요한 부분만 다운로드
- **Seek 최적화**: faststart 플래그로 메타데이터를 앞쪽에 배치
- **버퍼링 전략**: 3-5초 선행 버퍼링으로 끊김 방지

#### 네트워크 적응형 재생
```javascript
// 네트워크 상태에 따른 품질 조정 (향후 HLS 확장 시)
const adaptiveStreaming = {
  wifi: '80kbps',      // 고품질
  cellular: '56kbps',  // 표준 품질  
  slow: '32kbps'       // 저품질 (향후 추가)
};
```

### 14.3 차기 확장 설계 포인트

* **HLS(AES-128)로 전환**: `-hls_time 4 -hls_playlist_type vod -hls_key_info_file ...`
* **멀티 비트레이트 레더**: 32/56/80 kbps 등 변형 m3u8
* **오프라인 캐시**: 앱 내부 암호화 저장 + 만료/기기 바인딩
* **접근성 강화**: 챕터·문단 북마크, 음성/제스처 기반 탐색
* **CDN 최적화**: 지역별 엣지 캐싱으로 지연시간 최소화

---

## 15. URL 설계 가이드 (로컬/프로덕션)

### 15.1 스토리지 키 표준

- 기본 규칙: `book/<book_id>/<prefix>/<filename>`
  - `<prefix>`: `uploads` | `media` | `covers`
  - 예시:
    - 원본 업로드: `book/123/uploads/0001.wav`
    - 인코딩 결과: `book/123/media/0001.m4a`
    - 표지 이미지: `book/123/covers/cover.jpg`

### 15.2 로컬 스트리밍/다운로드 URL

- 단일 경로: `GET /api/v1/files/{file_key}`
  - 예: `GET /api/v1/files/book/123/media/0001.m4a`
  - Range 지원: `Range: bytes=START-END` → 206 Partial Content, `Content-Range` 헤더 반환
  - 전체 전송 시: 200 OK, `Accept-Ranges: bytes`

### 15.3 프로덕션 스트리밍 URL

- 챕터 스트리밍 요청: `GET /api/v1/audio/{book_id}/chapters/{chapter_id}/stream`
  - 내부 키 결정 우선순위: `file_info.s3_key` → `book/<book_id>/media/<original_name>` → fallback(`chapter_id.m4a`)
  - URL 생성 우선순위: CloudFront Signed URL(60~120초) → S3 Pre-signed GET(폴백)
  - 응답 예: `{ "streaming_url": "https://<cf_domain>/book/123/media/0001.m4a?Signature=...", "expires_at": "...", "duration": 1800 }`

### 15.4 업로드 URL (프로덕션)

- Pre-signed PUT: `GET /api/v1/files/presigned-upload-url?user_id=...&book_id=...&filename=...&content_type=...&file_type=uploads|media|cover`
  - 응답: `{ upload_url, key, file_id, expires_in }`
  - 업로드 완료 후 클라이언트는 `key`를 보존하여 후속 처리(메타 저장/인코딩 트리거)에 사용

### 15.5 권한/보안

- 모든 다운로드/스트리밍/목록/정보는 인증 필요
- 업로드 권한: `admin|editor` 스코프 필요
- 삭제 권한: 파일 삭제는 `admin` 스코프 필요, 도메인 오브젝트 삭제는 소유권 검증

### 최종 한 줄 요약

\*\*S3 비공개 + CloudFront(OAC, Signed URL) + FFmpeg 단일 프리셋(AAC-LC 56kbps 모노)\*\*로 시작하면, 50 동시접속 규모에서 **보안·성능·비용** 모두 안정적으로 MVP를 빠르게 띄울 수 있습니다.