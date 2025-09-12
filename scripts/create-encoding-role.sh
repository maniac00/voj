#!/bin/bash
# 인코딩용 Lambda 역할 생성 스크립트 (관리자 권한 필요)

set -e

echo "🎵 인코딩용 Lambda 역할 생성 중..."

# 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_NAME="voj-lambda-encoding-role"
POLICY_NAME="voj-lambda-encoding-policy"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

# 1. 인코딩용 Lambda 역할 생성
echo "📋 인코딩용 Lambda 역할 생성: $ROLE_NAME"
if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    echo "ℹ️  $ROLE_NAME 역할이 이미 존재합니다."
else
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://aws-policies/lambda-api-trust-policy.json \
        --description "VOJ encoding Lambda execution role"
    echo "✅ $ROLE_NAME 역할 생성 완료"
fi

# 2. 인코딩용 Lambda 정책 생성
echo "📋 인코딩용 Lambda 정책 생성: $POLICY_NAME"
if aws iam get-policy --policy-arn "$POLICY_ARN" >/dev/null 2>&1; then
    echo "ℹ️  $POLICY_NAME 정책이 이미 존재합니다."
else
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://aws-policies/lambda-encoding-policy.json \
        --description "VOJ encoding Lambda permissions policy"
    echo "✅ $POLICY_NAME 정책 생성 완료"
fi

# 3. 커스텀 정책을 역할에 연결
echo "🔗 커스텀 정책을 역할에 연결 중..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"
echo "✅ 커스텀 정책 연결 완료"

# 4. 기본 Lambda 실행 정책 연결
echo "🔗 기본 Lambda 실행 정책 연결 중..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
echo "✅ 기본 Lambda 실행 정책 연결 완료"

echo ""
echo "🎉 인코딩용 Lambda 역할 설정 완료!"
echo "📝 역할 ARN: arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo ""
echo "📋 연결된 정책 확인:"
aws iam list-attached-role-policies --role-name "$ROLE_NAME"


