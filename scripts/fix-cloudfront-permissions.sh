#!/bin/bash

# CloudFront 키 그룹 조회 권한 추가 스크립트 (관리자 권한 필요)
# 사용법: ./fix-cloudfront-permissions.sh [profile-name]

set -e

PROFILE=${1:-"admin"}
USER_NAME="voj-dev"
POLICY_NAME="VOJCloudFrontKeyGroupReadPolicy"

echo "🔐 CloudFront 키 그룹 조회 권한 추가 중..."
echo "Profile: $PROFILE"
echo "User: $USER_NAME"
echo "Policy: $POLICY_NAME"
echo ""

# 정책 문서 생성
cat > /tmp/cloudfront-keygroup-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:ListKeyGroups",
        "cloudfront:GetKeyGroup",
        "cloudfront:ListPublicKeys",
        "cloudfront:GetPublicKey"
      ],
      "Resource": "*"
    }
  ]
}
EOF

echo "1. 정책 생성 중..."
POLICY_ARN=$(AWS_PROFILE=$PROFILE aws iam create-policy \
  --policy-name $POLICY_NAME \
  --policy-document file:///tmp/cloudfront-keygroup-policy.json \
  --description "CloudFront key group read access for VOJ project" \
  --query 'Policy.Arn' --output text 2>/dev/null || \
  AWS_PROFILE=$PROFILE aws iam list-policies \
  --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text)

echo "   ✅ 정책 ARN: $POLICY_ARN"

echo "2. 사용자에게 정책 연결 중..."
AWS_PROFILE=$PROFILE aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn $POLICY_ARN

echo "   ✅ 정책 연결 완료"
echo ""

echo "🎉 CloudFront 키 그룹 조회 권한 추가 완료!"
echo ""
echo "이제 voj-dev 사용자로 다음 명령어들을 실행할 수 있습니다:"
echo ""
echo "# 모든 키 그룹 조회"
echo "aws cloudfront list-key-groups"
echo ""
echo "# 특정 키 그룹 조회"
echo "aws cloudfront get-key-group --id da9e785e-e204-4932-b474-95e16ba3a350"
echo ""
echo "# voj-key-group만 조회"
echo "aws cloudfront list-key-groups --query 'KeyGroupList.Items[?Name==\`voj-key-group\`]'"

# 임시 파일 정리
rm -f /tmp/cloudfront-keygroup-policy.json

echo ""
echo "🔍 키 그룹 확인을 위해 다음 명령어를 실행해보세요:"
echo "aws cloudfront get-key-group --id da9e785e-e204-4932-b474-95e16ba3a350"


