# ECS 배포 템플릿 가이드

## 필요한 값(예시)

- AWS_ACCOUNT_ID: 529088277581
- AWS_REGION: ap-northeast-2
- ECR_REPO: voj-backend
- ECS_CLUSTER: voj-prod
- ECS_SERVICE: voj-backend-api
- EXECUTION_ROLE_ARN: arn:aws:iam::<account>:role/voj-ecs-execution
- TASK_ROLE_ARN: arn:aws:iam::<account>:role/voj-backend-task
- ALB Target Group health path: /api/v1/health

`taskdef.json`의 `<account>` 문자열을 실제 계정 ID로 바꾸세요.

## GitHub Actions 연동

워크플로우: `.github/workflows/backend-deploy.yml`

- GitHub Secrets:
  - `AWS_IAM_ROLE_ARN`: OIDC로 Assume할 배포용 역할 ARN

배포 순서: 빌드 → ECR 푸시 → 태스크 정의 렌더 → ECS 서비스 업데이트.


