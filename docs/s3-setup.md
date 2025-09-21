# S3 버킷 구성 가이드 (프로덕션)

체크리스트 3.0 항목을 완료할 때 참고하세요. 대상 버킷: `voj-audiobooks-prod`

## 1. 버킷 생성 (3.1)

```bash
aws s3api create-bucket \
  --bucket voj-audiobooks-prod \
  --region ap-northeast-2 \
  --create-bucket-configuration LocationConstraint=ap-northeast-2
```

- Block Public Access는 생성 시 기본값(ON)을 유지
- 버전 관리는 필요 시 활성화 (MVP에서는 옵션)

## 2. 암호화 설정 (3.2)

```bash
aws s3api put-bucket-encryption \
  --bucket voj-audiobooks-prod \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

- SSE-S3(AES256)를 기본으로 사용
- KMS를 사용할 경우 `SSEAlgorithm`을 `aws:kms`, `KMSMasterKeyID`를 지정

## 3. CORS 정책 (3.3)

`cors.json` 예시:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD", "PUT"],
    "AllowedOrigins": [
      "https://main.dxxxxxxxx.amplifyapp.com",
      "https://voj-audiobooks.vercel.app",
      "https://api.voj-audiobook.com"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 86400
  }
]
```

적용 명령:
```bash
aws s3api put-bucket-cors --bucket voj-audiobooks-prod --cors-configuration file://cors.json
```

## 4. 버킷 정책 및 OAC 연동 (3.4)

CloudFront Origin Access Control(OAC) ID가 `E2L8IJM40TUC0U`인 경우 정책 예시:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontOAC",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::voj-audiobooks-prod/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::529088277581:distribution/ESZTOMYA7BE5"
        }
      }
    }
  ]
}
```

적용 명령:
```bash
aws s3api put-bucket-policy --bucket voj-audiobooks-prod --policy file://policy.json
```

## 5. 수명주기/버전 관리 (3.5)

- 저장 공간 최적화를 위해 Lifecycle rule 예시 (선택):

```json
{
  "Rules": [
    {
      "ID": "ExpireUploads",
      "Status": "Enabled",
      "Prefix": "book/",  
      "Transitions": [
        {"Days": 180, "StorageClass": "GLACIER"}
      ]
    }
  ]
}
```

- 대용량 오디오 보관 정책에 맞춰 수정

## 6. 검증 체크리스트

- [ ] Block Public Access = ON
- [ ] 기본 암호화 = AES256 (또는 KMS)
- [ ] CORS 정책 적용 완료, 허용 Origin 최소화
- [ ] 버킷 정책이 CloudFront OAC에만 GetObject 허용
- [ ] 테스트: CloudFront Signed URL은 작동하지만 S3 프리사인 URL은 403 반환

필요 시 `docs/verify-streaming.md`, `docs/security-checklist.md`와 연동해 스트리밍, 보안 점검을 수행하세요.
