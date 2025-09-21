#!/bin/bash
# DEPRECATED: Lambda 배포 경로는 ECR/ECS/ALB로 전환되었습니다. 유지보수 중단.
# Lambda IAM 역할 생성 스크립트 (관리자 권한 필요)

set -e

echo "🔐 Lambda IAM 역할 생성 중..."

# 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. API용 Lambda 역할 생성
echo "📋 API용 Lambda 역할 생성 중..."

# 역할이 이미 존재하는지 확인
if aws iam get-role --role-name "voj-lambda-api-role" >/dev/null 2>&1; then
    echo "ℹ️  voj-lambda-api-role 역할이 이미 존재합니다."
else
    aws iam create-role \
        --role-name "voj-lambda-api-role" \
        --assume-role-policy-document file://aws-policies/lambda-api-trust-policy.json \
        --description "VOJ API Lambda execution role"
    echo "✅ voj-lambda-api-role 역할 생성 완료"
fi

# 2. API용 Lambda 정책 생성
echo "📋 API용 Lambda 정책 생성 중..."

# 정책이 이미 존재하는지 확인
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/voj-lambda-api-policy"
if aws iam get-policy --policy-arn "$POLICY_ARN" >/dev/null 2>&1; then
    echo "ℹ️  voj-lambda-api-policy 정책이 이미 존재합니다."
else
    aws iam create-policy \
        --policy-name "voj-lambda-api-policy" \
        --policy-document file://aws-policies/lambda-api-policy.json \
        --description "VOJ API Lambda permissions policy"
    echo "✅ voj-lambda-api-policy 정책 생성 완료"
fi

# 3. 정책을 역할에 연결
echo "🔗 정책을 역할에 연결 중..."
aws iam attach-role-policy \
    --role-name "voj-lambda-api-role" \
    --policy-arn "$POLICY_ARN"

# 4. 기본 Lambda 실행 정책도 연결
aws iam attach-role-policy \
    --role-name "voj-lambda-api-role" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

echo ""
echo "🎉 API용 Lambda 역할 설정 완료!"
echo "📝 역할 ARN: arn:aws:iam::${ACCOUNT_ID}:role/voj-lambda-api-role"

echo ""
echo "📋 연결된 정책 확인:"
aws iam list-attached-role-policies --role-name "voj-lambda-api-role"
