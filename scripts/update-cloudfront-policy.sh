#!/bin/bash

# CloudFront 키 그룹 권한을 기존 정책에 추가하는 스크립트 (관리자 권한 필요)
# 사용법: ./update-cloudfront-policy.sh [profile-name]

set -e

PROFILE=${1:-"admin"}
POLICY_NAME="VOJDeveloperAllInOnePolicy"
POLICY_FILE="aws-policies/voj-dev-policy.json"

echo "🔄 CloudFront 키 그룹 권한을 기존 정책에 추가 중..."
echo "Profile: $PROFILE"
echo "Policy: $POLICY_NAME"
echo "Policy File: $POLICY_FILE"
echo ""

# 현재 정책 ARN 조회
echo "1. 정책 ARN 조회 중..."
POLICY_ARN=$(AWS_PROFILE=$PROFILE aws iam list-policies \
  --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text)

if [ -z "$POLICY_ARN" ]; then
    echo "❌ 정책 '$POLICY_NAME'을 찾을 수 없습니다."
    exit 1
fi

echo "   ✅ 정책 ARN: $POLICY_ARN"

# 새 정책 버전 생성
echo "2. 새 정책 버전 생성 중..."
NEW_VERSION=$(AWS_PROFILE=$PROFILE aws iam create-policy-version \
  --policy-arn $POLICY_ARN \
  --policy-document file://$POLICY_FILE \
  --set-as-default \
  --query 'PolicyVersion.VersionId' --output text)

echo "   ✅ 새 정책 버전: $NEW_VERSION"

echo ""
echo "🎉 CloudFront 키 그룹 권한 추가 완료!"
echo ""
echo "추가된 권한:"
echo "- cloudfront:CreateKeyGroup"
echo "- cloudfront:GetKeyGroup"
echo "- cloudfront:UpdateKeyGroup"
echo "- cloudfront:DeleteKeyGroup"
echo "- cloudfront:ListKeyGroups"
echo ""
echo "🔍 이제 다음 명령어로 키 그룹을 확인할 수 있습니다:"
echo ""
echo "# 특정 키 그룹 조회"
echo "aws cloudfront get-key-group --id da9e785e-e204-4932-b474-95e16ba3a350"
echo ""
echo "# voj-key-group 필터링"
echo "aws cloudfront list-key-groups --query 'KeyGroupList.Items[?Name==\`voj-key-group\`]'"
echo ""
echo "💡 권한이 적용되는데 몇 분 정도 걸릴 수 있습니다."


