# Frontend (Next.js) 프로덕션 배포 가이드 – AWS 환경

이 문서는 Next.js 어드민 프론트를 **AWS Amplify Hosting + CloudFront** 조합으로 배포하는 절차를 설명합니다. Git 연동 대신 S3/CloudFront 수동 배포를 선택할 수도 있으므로 두 방식을 모두 정리했습니다.

## 1. 사전 준비

- AWS 계정 및 콘솔 접근 권한 (리전: `ap-northeast-2` 기준)
- AWS CLI v2 및 Amplify CLI 설치(선택사항)
- GitHub(또는 CodeCommit) 저장소 접근 권한
- 백엔드 API가 `https://api.voj-audiobook.com`에서 정상 동작 중이어야 함

### 필수 환경 변수

`frontend/.env.production.example` 파일을 참고해 다음 값을 설정합니다. Amplify Console의 **App settings → Environment variables**에도 동일하게 입력하세요.

| 변수 | 설명 | 예시 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | API Gateway 루트 URL | `https://api.voj-audiobook.com` |
| `NEXT_PUBLIC_API_BASE` | API v1 엔드포인트 | `https://api.voj-audiobook.com/api/v1` |

> 도메인을 변경할 경우 백엔드 `ALLOWED_HOSTS` 목록도 함께 업데이트 해야 합니다.

## 2. 로컬 프로덕션 빌드 검증

```bash
cd frontend
cp .env.production.example .env.production  # 필요 시
npm ci
npm run build
npm run start
```

- 빌드가 성공해야 하며 `http://localhost:3000`에서 로그인 → 책 목록 조회까지 확인합니다.
- 문제 발생 시 로컬에서 수정 후 다시 빌드한 뒤 원격 배포를 진행합니다.

## 3. AWS Amplify Hosting 배포

### 3.1 애플리케이션 생성

1. AWS 콘솔 → **Amplify Hosting** → **New app → Host web app** 선택
2. GitHub/CodeCommit 등 저장소를 연결하고 브랜치를 지정합니다 (예: `main`).

### 3.2 Build 설정 (`amplify.yml`)

다음 설정을 저장소 루트에 추가하면 Amplify가 Next.js 앱을 빌드합니다.

```yaml
version: 1
applications:
  - appRoot: frontend
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: .next
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
```

> Next.js 13+ (App Router) SSR을 사용하므로 Amplify가 자동으로 서버 함수와 정적 자산을 배포합니다.

### 3.3 환경 변수 설정

Amplify Console → **App settings → Environment variables**에서 위 표의 값을 입력하고 **Save** 후 새 빌드를 트리거합니다.

### 3.4 배포 완료 후 확인 사항

- Amplify에서 제공하는 기본 도메인(예: `https://main.dxxxxxxxx.amplifyapp.com`)을 복사합니다.
- 백엔드 `ALLOWED_HOSTS`와 CloudFront CORS 설정에 해당 도메인을 추가했는지 확인합니다.
- 브라우저에서 Amplify 도메인으로 접속하여 로그인 → 대시보드 → 책 목록 흐름을 검증합니다.

## 4. 수동 배포 (S3 + CloudFront)

Amplify 대신 S3 정적 호스팅과 CloudFront 배포를 사용할 수도 있습니다.

### 4.1 빌드 & Export

```bash
cd frontend
npm run build
npm run export  # out/ 폴더 생성
```

### 4.2 S3 업로드

```bash
aws s3 sync out/ s3://voj-frontend-prod --delete --profile <profile>
```

- S3 버킷은 **Static website hosting**을 비활성화하고 CloudFront를 통해서만 접근하도록 구성합니다.

### 4.3 CloudFront 배포

- 오리진: `voj-frontend-prod` 버킷 + Origin Access Control(OAC)
- 캐시 정책: 정적 자산 캐시, `/index.html` 등 SPA 라우팅을 위한 캐시 무효화 정책 설정
- 배포 후 사용자용 도메인(CNAME)을 연결합니다.

### 4.4 파이프라인 자동화 (선택)

- AWS CodePipeline 또는 GitHub Actions에서 `npm run build && npm run export` 후 S3에 업로드하도록 구성합니다.
- `aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"` 명령으로 캐시 무효화를 자동화합니다.

## 5. 스모크 테스트 체크리스트

1. `/login` 화면에서 관리자 계정으로 로그인 가능
2. `/books` 목록이 표시되고 CRUD가 정상 동작
3. 오디오 업로드 → 스트리밍 URL 발급 → 플레이어 재생까지 확인
4. 브라우저 콘솔 및 네트워크 탭에서 CORS 오류 없음
5. CloudFront 로그/Amplify 모니터링에서 4xx/5xx 비율이 비정상적으로 높지 않음

## 6. 문제 해결 가이드

- **401/403 발생**: 백엔드 `SIMPLE_AUTH_*` 값 확인 및 토큰 만료 여부 점검
- **CORS 오류**: 백엔드 `ALLOWED_HOSTS`, CloudFront CORS 정책, S3 CORS 정책을 재검토
- **API URL 오타**: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_API_BASE`가 실제 API Gateway 도메인인지 확인
- **배포 실패**: Amplify 빌드 로그에서 `npm run build` 단계 오류 확인 후 수정
- **정적 자산 미반영**: CloudFront 캐시 무효화 실행 (`scripts/cf-invalidate.sh` 참고)

## 7. 참고 자료

- AWS Amplify Hosting 문서: <https://docs.aws.amazon.com/amplify/latest/userguide/welcome.html>
- Next.js on Amplify 베스트 프랙티스: <https://docs.aws.amazon.com/amplify/latest/userguide/ssr-with-amplify.html>
- S3 + CloudFront 배포 패턴: <https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.html>
