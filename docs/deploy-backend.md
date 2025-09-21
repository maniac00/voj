# Backend 컨테이너 배포 가이드 (ECR + ECS Fargate + ALB)

본 문서는 기존 Lambda/API Gateway 기반 배포를 중단하고, FastAPI를 컨테이너로 패키징하여 ECR → ECS(Fargate) → ALB(HTTPS)로 배포하는 절차를 정리합니다.

## 0. 아키텍처 개요

- **ECR**: `voj-backend` 리포지토리. 이미지 태그: `sha-<short>` 또는 릴리즈 태그
- **ECS(Fargate)**: 2개 AZ, Desired=2, CPU 0.5vCPU / Mem 1GB(초기)
- **ALB**: Listener 443(ACM), Target Group HTTP 8000, 헬스체크 `/api/v1/health`
- **Route53**: `api.voj-audiobook.com` → ALB
- **Secrets/Params**: SSM Parameter Store / Secrets Manager로 환경변수 관리
- **Logs**: CloudWatch Logs로 앱 로그 수집

## 1. Docker 이미지 빌드

```bash
# 백엔드 루트(/backend) 기준 Dockerfile 사용 예정
docker buildx build \
  --platform linux/amd64 \
  -t <account>.dkr.ecr.ap-northeast-2.amazonaws.com/voj-backend:sha-$(git rev-parse --short HEAD) \
  -f backend/Dockerfile \
  .
```

## 2. ECR 리포지토리 준비 및 푸시

```bash
aws ecr create-repository --repository-name voj-backend --region ap-northeast-2 || true
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.ap-northeast-2.amazonaws.com

TAG=sha-$(git rev-parse --short HEAD)
REPO=<account>.dkr.ecr.ap-northeast-2.amazonaws.com/voj-backend
docker push ${REPO}:${TAG}
```

## 3. ECS 태스크 정의 (요점)

- 컨테이너 포트: 8000
- 명령: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers 2 --timeout 60`
- Env: SSM/Secrets에서 주입(예: `ENVIRONMENT=production`, `AWS_REGION=ap-northeast-2`, `BOOKS_TABLE_NAME`, `AUDIO_CHAPTERS_TABLE_NAME`, `S3_BUCKET_NAME` 등)
- 로그 드라이버: awslogs

예시 스니펫(JSON):

```json
{
  "family": "voj-backend-prod",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account>.dkr.ecr.ap-northeast-2.amazonaws.com/voj-backend:sha-<short>",
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "command": [
        "gunicorn","app.main:app","-k","uvicorn.workers.UvicornWorker",
        "-b","0.0.0.0:8000","--workers","2","--timeout","60"
      ],
      "environment": [],
      "secrets": [
        {"name": "S3_BUCKET_NAME", "valueFrom": "arn:aws:ssm:ap-northeast-2:<account>:parameter/voj/prod/S3_BUCKET_NAME"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/voj-backend",
          "awslogs-region": "ap-northeast-2",
          "awslogs-stream-prefix": "api"
        }
      }
    }
  ]
}
```

## 4. ALB/타깃그룹 설정

- Target Group 프로토콜 HTTP, Port 8000, 헬스체크 Path: `/api/v1/health`
- Listener 443(ACM 인증서 연결) → TG 포워드
- 보안그룹: ALB(0.0.0.0/0 :443), ECS(소스 ALB SG만 인바운드 8000 허용)

## 5. Route53

- `api.voj-audiobook.com` A-ALIAS → ALB DNS

## 6. 권한/IAM

- Execution Role: ECR Pull, CW Logs
- Task Role: S3/DynamoDB/Secrets 최소권한

## 7. 배포 순서(수동)

1) Docker 이미지 빌드/푸시(ECR)
2) ECS Task Definition 등록/갱신 → 서비스 업데이트
3) ALB Listener/TG 연결 상태 확인(헬스 체크 200)
4) Route53 도메인 연결 및 HTTPS 확인

## 8. 문제 해결 팁

- 컨테이너 시작 커맨드는 gunicorn 권장(멀티워커, graceful)
- 헬스체크 실패 시: 보안그룹/서브넷 라우팅, 헬스 Path, 앱 기동 로그 확인
- CORS/TrustedHost는 ALB 도메인과 프론트 도메인만 허용

## 부록: 환경변수 예시(.env.production)

```bash
ENVIRONMENT=production
AWS_REGION=ap-northeast-2
BOOKS_TABLE_NAME=voj-books-prod
AUDIO_CHAPTERS_TABLE_NAME=voj-audio-chapters-prod
S3_BUCKET_NAME=voj-audiobooks-prod
CORS_ORIGINS=https://voj-audiobooks.vercel.app,https://admin.example.com
ALLOWED_HOSTS=api.voj-audiobook.com
```
