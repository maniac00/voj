#!/bin/bash
# 커스텀 IAM 정책 생성 및 연결 스크립트 (관리자 권한 필요)

set -e

USER_NAME="voj-dev"
POLICY_NAME="VOJDeveloperPolicy"
POLICY_FILE="aws-policies/voj-dev-policy.json"

echo "🔐 커스텀 IAM 정책 생성 중..."

# 1. 정책 생성
echo "📋 정책 생성: $POLICY_NAME"
POLICY_ARN=$(aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file://"$POLICY_FILE" \
    --description "VOJ 오디오북 프로젝트 개발자 권한" \
    --query 'Policy.Arn' \
    --output text)

if [ $? -eq 0 ]; then
    echo "✅ 정책 생성 완료: $POLICY_ARN"
else
    echo "❌ 정책 생성 실패. 이미 존재하는 정책일 수 있습니다."
    # 기존 정책 ARN 가져오기
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
fi

# 2. 사용자에게 정책 연결
echo "🔗 사용자에게 정책 연결 중..."
aws iam attach-user-policy \
    --user-name "$USER_NAME" \
    --policy-arn "$POLICY_ARN"

if [ $? -eq 0 ]; then
    echo "✅ 정책 연결 완료"
else
    echo "❌ 정책 연결 실패"
    exit 1
fi

echo ""
echo "🎉 커스텀 정책 설정 완료!"
echo "📝 연결된 정책 확인:"
aws iam list-attached-user-policies --user-name "$USER_NAME"

