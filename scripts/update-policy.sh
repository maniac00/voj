#!/bin/bash
# 기존 정책 업데이트 스크립트 (관리자 권한 필요)

set -e

POLICY_NAME="VOJDeveloperAllInOnePolicy"
POLICY_FILE="aws-policies/voj-dev-policy.json"

echo "🔄 IAM 정책 업데이트 중..."

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
    echo "✅ 정책 업데이트 완료"
else
    echo "❌ 정책 업데이트 실패"
    exit 1
fi

echo ""
echo "🎉 정책 업데이트 성공!"
echo "🔍 DynamoDB 권한 테스트를 해보세요:"
echo "  aws dynamodb list-tables"


