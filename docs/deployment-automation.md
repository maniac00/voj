# 배포 자동화 및 롤백 전략 (ECR/ECS/ALB)

## 1. CI/CD 개요

### 목표
- 백엔드 컨테이너(ECR) → ECS(Fargate) → ALB 배포 자동화
- main 브랜치 머지 시 프로덕션 배포, 태그 기반 릴리즈 가능
- 빠른 롤백: 이전 태스크 정의 리비전으로 즉시 복구

### 도구 제안
- **GitHub Actions**: 파이프라인 구성(OIDC 권장)
- **Amazon ECS**: 배포 대상, 롤링 업데이트
- **ECR**: 컨테이너 레지스트리

## 2. 백엔드 파이프라인 (GitHub Actions 예시)

```yaml
name: Deploy Backend (ECR→ECS)

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-deploy.yml'
      - 'pyproject.toml'

jobs:
  build-and-deploy:
    permissions:
      id-token: write
      contents: read
    runs-on: ubuntu-latest
    env:
      AWS_REGION: ap-northeast-2
      ECR_REPO: voj-backend
      ECS_CLUSTER: voj-prod
      ECS_SERVICE: voj-backend-api
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_IAM_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        run: |
          TAG=sha-$(git rev-parse --short HEAD)
          docker buildx build \
            --platform linux/amd64 \
            -t $ECR_REGISTRY/${{ env.ECR_REPO }}:$TAG \
            -f backend/Dockerfile .
          docker push $ECR_REGISTRY/${{ env.ECR_REPO }}:$TAG
          echo "IMAGE=$ECR_REGISTRY/${{ env.ECR_REPO }}:$TAG" >> $GITHUB_ENV

      - name: Render new task definition
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: .github/ecs/taskdef.json
          container-name: api
          image: ${{ env.IMAGE }}

      - name: Deploy Amazon ECS task definition
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true
```

설명:
- OIDC로 AWS 자격증명 없이 배포 롤을 가정
- `backend/Dockerfile`로 빌드, ECR에 푸시 후 태스크 정의에 이미지만 교체
- 태스크 정의 템플릿은 `.github/ecs/taskdef.json`에서 관리

## 3. 태스크 정의 템플릿(.github/ecs/taskdef.json) 예시

```json
{
  "family": "voj-backend-prod",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account>:role/voj-ecs-execution",
  "taskRoleArn": "arn:aws:iam::<account>:role/voj-backend-task",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<to-be-replaced>",
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "command": [
        "gunicorn","app.main:app","-k","uvicorn.workers.UvicornWorker",
        "-b","0.0.0.0:8000","--workers","2","--timeout","60"
      ],
      "essential": true,
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "AWS_REGION", "value": "ap-northeast-2"}
      ],
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

## 4. 롤백 전략

- ECS 서비스의 이전 태스크 정의 리비전으로 재배포
- 문제 발생 시 Route53 가중치를 0%로 원복(기존 경로 유지 시)

## 5. 필요 시크릿/변수 목록

- GitHub Secrets: `AWS_IAM_ROLE_ARN`
- SSM/Secrets: `S3_BUCKET_NAME`, `BOOKS_TABLE_NAME`, `AUDIO_CHAPTERS_TABLE_NAME`, `CORS_ORIGINS`, `ALLOWED_HOSTS` 등

## 6. 참고
- GitHub OIDC: <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html>
- ECS Deploy Action: <https://github.com/aws-actions/amazon-ecs-deploy-task-definition>
