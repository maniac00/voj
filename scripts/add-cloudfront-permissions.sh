#!/bin/bash

# CloudFront Key Group 권한 추가 스크립트 (관리자 권한 필요)
# 사용법: ./add-cloudfront-permissions.sh [profile-name]

set -e

PROFILE=${1:-"admin"}
USER_NAME="voj-dev"
POLICY_NAME="VOJCloudFrontKeyGroupPolicy"

echo "🔐 CloudFront 키 그룹 권한 추가 중..."
echo "Profile: $PROFILE"
echo "User: $USER_NAME"
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

echo "정책 생성 중..."
POLICY_ARN=$(AWS_PROFILE=$PROFILE aws iam create-policy \
  --policy-name $POLICY_NAME \
  --policy-document file:///tmp/cloudfront-keygroup-policy.json \
  --query 'Policy.Arn' --output text 2>/dev/null || \
  AWS_PROFILE=$PROFILE aws iam list-policies \
  --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text)

echo "정책 ARN: $POLICY_ARN"

echo "사용자에게 정책 연결 중..."
AWS_PROFILE=$PROFILE aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn $POLICY_ARN

echo "✅ CloudFront 키 그룹 권한 추가 완료!"
echo ""
echo "이제 다음 명령어로 키 그룹을 확인할 수 있습니다:"
echo "aws cloudfront get-key-group --id da9e785e-e204-4932-b474-95e16ba3a350"

# 임시 파일 정리
rm -f /tmp/cloudfront-keygroup-policy.json


