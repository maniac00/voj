#!/bin/bash
# DynamoDB 태그 권한 추가 스크립트 (관리자 권한 필요)

set -e

echo "🏷️  DynamoDB 태그 권한 추가 중..."

POLICY_NAME="VOJDeveloperAllInOnePolicy"
POLICY_FILE="aws-policies/voj-dev-policy.json"

# 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

echo "📋 정책 업데이트: $POLICY_NAME"

# 새 정책 버전 생성
aws iam create-policy-version \
    --policy-arn "$POLICY_ARN" \
    --policy-document file://"$POLICY_FILE" \
    --set-as-default

if [ $? -eq 0 ]; then
    echo "✅ DynamoDB 태그 권한 추가 완료"
else
    echo "❌ 정책 업데이트 실패"
    exit 1
fi

echo ""
echo "🎉 권한 업데이트 성공!"
echo "🔍 DynamoDB 태그 권한 테스트:"
echo "  aws dynamodb create-table --table-name test-table --attribute-definitions AttributeName=id,AttributeType=S --key-schema AttributeName=id,KeyType=HASH --billing-mode PAY_PER_REQUEST --tags Key=Test,Value=Value"


