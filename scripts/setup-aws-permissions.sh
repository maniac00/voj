#!/bin/bash
# AWS IAM 권한 설정 스크립트 (관리자 권한 필요)

set -e

USER_NAME="voj-dev"
POLICIES=(
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
    "arn:aws:iam::aws:policy/AmazonCognitoPowerUser"
    "arn:aws:iam::aws:policy/CloudFrontFullAccess"
    "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
    "arn:aws:iam::aws:policy/AmazonS3FullAccess"
    "arn:aws:iam::aws:policy/APIGatewayAdministrator"
    "arn:aws:iam::aws:policy/IAMReadOnlyAccess"
)

echo "🔐 voj-dev 사용자에게 개발 권한 추가 중..."

for policy in "${POLICIES[@]}"; do
    policy_name=$(basename "$policy")
    echo "📋 정책 연결 중: $policy_name"
    
    aws iam attach-user-policy \
        --user-name "$USER_NAME" \
        --policy-arn "$policy"
    
    if [ $? -eq 0 ]; then
        echo "✅ $policy_name 연결 완료"
    else
        echo "❌ $policy_name 연결 실패"
    fi
done

echo ""
echo "🎉 권한 설정 완료!"
echo "📝 설정된 정책 확인:"
aws iam list-attached-user-policies --user-name "$USER_NAME"

