#!/bin/bash
# IAM 그룹을 통한 권한 관리 (관리자 권한 필요)

set -e

USER_NAME="voj-dev"
GROUP_NAME="voj-developers"
POLICY_NAME="VOJDeveloperAllInOnePolicy"

echo "👥 IAM 그룹을 통한 권한 관리 설정 중..."

# 1. 개발자 그룹 생성
echo "📋 개발자 그룹 생성: $GROUP_NAME"
aws iam create-group --group-name "$GROUP_NAME" || echo "그룹이 이미 존재할 수 있습니다."

# 2. 그룹에 통합 정책 연결
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

echo "🔗 그룹에 정책 연결 중..."
aws iam attach-group-policy \
    --group-name "$GROUP_NAME" \
    --policy-arn "$POLICY_ARN"

# 3. 사용자를 그룹에 추가
echo "👤 사용자를 그룹에 추가 중..."
aws iam add-user-to-group \
    --group-name "$GROUP_NAME" \
    --user-name "$USER_NAME"

echo ""
echo "🎉 IAM 그룹 설정 완료!"
echo "📝 그룹 멤버 확인:"
aws iam get-group --group-name "$GROUP_NAME"


