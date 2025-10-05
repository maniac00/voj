# 배포 자동화 및 롤백 전략 (Railway + Vercel)

## 1. CI/CD 개요

### 목표
- 백엔드 컨테이너를 Railway로 배포 자동화
- main 브랜치 머지 시 프로덕션 배포, 태그 기반 릴리즈 가능
- 빠른 롤백: Railway 배포 이전 버전으로 롤백

### 도구 제안
- **GitHub Actions**: Railway CLI 기반 파이프라인
- **Railway**: 컨테이너 배포 대상, 롤링 업데이트

## 2. 백엔드 파이프라인 (GitHub Actions 예시)

```yaml
name: Deploy Backend to Railway

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-deploy.yml'
      - 'pyproject.toml'

jobs:
  deploy-railway:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Railway CLI
        run: npm i -g @railway/cli

      - name: Deploy Backend to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --service backend --ci
```

설명:
- `Railway CLI`로 프로젝트/서비스 기준 배포를 수행합니다.
- GitHub Secrets에는 `RAILWAY_TOKEN`만 필요합니다.

## 3. 태스크 정의 템플릿

Railway는 별도의 ECS 태스크 정의가 필요 없습니다. `railway.json`과 프로젝트 설정을 사용합니다.

## 4. 롤백 전략

- Railway 대시보드에서 이전 배포로 롤백

## 5. 필요 시크릿/변수 목록

- GitHub Secrets: `RAILWAY_TOKEN`

## 6. 참고
- GitHub OIDC: <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html>
- ECS Deploy Action: <https://github.com/aws-actions/amazon-ecs-deploy-task-definition>
