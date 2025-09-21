#!/bin/bash
set -euo pipefail

# Lambda/API Gateway/CloudFront 알람 생성 스크립트 (기본 템플릿)
# usage: AWS_PROFILE=voj-prod ./scripts/create-cloudwatch-alarms.sh

REGION="${AWS_REGION:-ap-northeast-2}"
PROFILE="${AWS_PROFILE:-default}"
SNS_TOPIC_ARN="${SNS_TOPIC_ARN:-}"  # 예: arn:aws:sns:ap-northeast-2:123456789012:voj-prod-alarms

if [ -z "${SNS_TOPIC_ARN}" ]; then
  echo "SNS_TOPIC_ARN 환경 변수를 설정하세요." >&2
  exit 1
fi

function put_alarm() {
  local name="$1"; shift
  aws --profile "${PROFILE}" --region "${REGION}" cloudwatch put-metric-alarm --alarm-name "${name}" "$@"
}

echo "Lambda 에러 알람 생성"
put_alarm "voj-backend-api-Errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 3 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=voj-backend-api \
  --treat-missing-data missing \
  --alarm-actions "${SNS_TOPIC_ARN}"

echo "Lambda Throttles 알람 생성"
put_alarm "voj-backend-api-Throttles" \
  --metric-name Throttles \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=voj-backend-api \
  --treat-missing-data notBreaching \
  --alarm-actions "${SNS_TOPIC_ARN}"

echo "API Gateway 5XX 알람 생성"
put_alarm "voj-apigw-5xx" \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --dimensions Name=ApiId,Value=${API_GATEWAY_ID:-a1b2c3d4} \
  --treat-missing-data missing \
  --alarm-actions "${SNS_TOPIC_ARN}"

echo "CloudFront 5xx 에러율 알람 생성"
aws --profile "${PROFILE}" --region us-east-1 cloudwatch put-metric-alarm \
  --alarm-name "voj-cf-5xx" \
  --metric-name 5xxErrorRate \
  --namespace AWS/CloudFront \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --dimensions Name=DistributionId,Value=${CLOUDFRONT_DISTRIBUTION_ID:-ESZTOMYA7BE5} Name=Region,Value=Global \
  --treat-missing-data missing \
  --alarm-actions "${SNS_TOPIC_ARN}"

echo "알람 생성 완료"
