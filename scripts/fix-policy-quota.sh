#!/bin/bash
# 정책 할당량 문제 해결 스크립트 (관리자 권한 필요)

set -e

USER_NAME="voj-dev"
POLICY_NAME="VOJDeveloperAllInOnePolicy"
POLICY_FILE="aws-policies/voj-dev-policy.json"

echo "🔧 정책 할당량 문제 해결 중..."

# 1. 현재 연결된 정책 확인
echo "📋 현재 연결된 정책 확인:"
aws iam list-attached-user-policies --user-name "$USER_NAME" || echo "정책 조회 권한 없음"

echo ""
echo "⚠️  기존 불필요한 정책들을 제거하고 통합 정책을 생성합니다."
echo "❓ 계속 진행하시겠습니까? (y/N)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ 작업이 취소되었습니다."
    exit 1
fi

# 2. 통합 커스텀 정책 생성
echo "📋 통합 정책 생성: $POLICY_NAME"

# 계정 ID 가져오기
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 정책이 이미 존재하는지 확인
if aws iam get-policy --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}" >/dev/null 2>&1; then
    echo "ℹ️  정책이 이미 존재합니다. 업데이트합니다."
    
    # 기존 정책 버전 생성
    aws iam create-policy-version \
        --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}" \
        --policy-document file://"$POLICY_FILE" \
        --set-as-default
    
    echo "✅ 정책 업데이트 완료"
else
    # 새 정책 생성
    POLICY_ARN=$(aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://"$POLICY_FILE" \
        --description "VOJ 오디오북 프로젝트 통합 개발자 권한" \
        --query 'Policy.Arn' \
        --output text)
    
    echo "✅ 새 정책 생성 완료: $POLICY_ARN"
fi

# 3. 사용자에게 정책 연결
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

echo "🔗 사용자에게 통합 정책 연결 중..."
aws iam attach-user-policy \
    --user-name "$USER_NAME" \
    --policy-arn "$POLICY_ARN"

echo "✅ 정책 연결 완료"

echo ""
echo "🎉 정책 할당량 문제 해결 완료!"
echo "📝 최종 연결된 정책 확인:"
aws iam list-attached-user-policies --user-name "$USER_NAME"

echo ""
echo "🔍 권한 테스트를 위해 다음 명령어를 실행해보세요:"
echo "  aws dynamodb list-tables"
echo "  aws cognito-idp list-user-pools --max-results 10"


