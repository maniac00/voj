#!/bin/bash

# CloudFront Key Group 생성 스크립트 (관리자 권한 필요)
# 사용법: ./create-cloudfront-keygroup.sh [profile-name]

set -e

PROFILE=${1:-"admin"}
PUBLIC_KEY_ID="K1MOHSPPL0L417"
KEY_GROUP_NAME="voj-key-group"

echo "🔐 CloudFront 키 그룹 생성 중..."
echo "Profile: $PROFILE"
echo "Public Key ID: $PUBLIC_KEY_ID"
echo "Key Group Name: $KEY_GROUP_NAME"
echo ""

# 키 그룹 생성
echo "키 그룹 생성 중..."
KEY_GROUP_RESULT=$(AWS_PROFILE=$PROFILE aws cloudfront create-key-group \
  --key-group-config '{
    "Name": "'$KEY_GROUP_NAME'",
    "Items": ["'$PUBLIC_KEY_ID'"],
    "Comment": "VOJ Audiobooks key group for Signed URLs"
  }' 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ 키 그룹 생성 성공!"
    echo "$KEY_GROUP_RESULT"
    
    # 키 그룹 ID 추출
    KEY_GROUP_ID=$(echo "$KEY_GROUP_RESULT" | grep -o '"Id": "[^"]*"' | cut -d'"' -f4)
    echo ""
    echo "📋 키 그룹 정보:"
    echo "- Key Group ID: $KEY_GROUP_ID"
    echo "- Key Group Name: $KEY_GROUP_NAME"
    echo "- Public Key ID: $PUBLIC_KEY_ID"
    
    # 정보를 파일에 저장
    cat >> keys/cloudfront-keys-info.txt << EOF

=== Key Group Info (Updated: $(date)) ===
Key Group ID: $KEY_GROUP_ID
Key Group Name: $KEY_GROUP_NAME
Status: Created

Next Steps:
1. CloudFront 배포 업데이트하여 키 그룹 연결
2. Signed URL 생성 시 Key Group ID 사용
EOF
    
    echo ""
    echo "🚀 다음 단계:"
    echo "1. CloudFront 배포를 업데이트하여 키 그룹을 연결하세요"
    echo "2. 백엔드에서 Signed URL 생성 시 Key Group ID: $KEY_GROUP_ID 사용"
    
else
    echo "❌ 키 그룹 생성 실패:"
    echo "$KEY_GROUP_RESULT"
    exit 1
fi


