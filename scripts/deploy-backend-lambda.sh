#!/bin/bash
# DEPRECATED: Lambda 배포 경로는 ECR/ECS/ALB로 전환되었습니다. 유지보수 중단.
set -euo pipefail

# Deploys the packaged backend Lambda and optionally redeploys API Gateway.
# Requirements:
#   - AWS CLI v2
#   - An existing Lambda function (name via $LAMBDA_FUNCTION_NAME)
#   - Packaged artifact at dist/backend_lambda.zip (or override via $LAMBDA_PACKAGE)
#   - Optional: env.production with key=value pairs for Lambda environment
#   - Optional: API Gateway HTTP API identifiers via $API_GATEWAY_ID / $API_STAGE_NAME

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PACKAGE_PATH="${LAMBDA_PACKAGE:-${REPO_ROOT}/dist/backend_lambda.zip}"
ENV_FILE="${LAMBDA_ENV_FILE:-${REPO_ROOT}/.env.production}"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
AWS_PROFILE="${AWS_PROFILE:-default}"
FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-voj-backend-api}"
API_ID="${API_GATEWAY_ID:-}"  # optional
API_STAGE="${API_STAGE_NAME:-prod}"  # optional
HANDLER_NAME_DEFAULT="backend.app.handler.handler"

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI가 설치되어 있지 않습니다." >&2
  exit 1
fi

if [ ! -f "${PACKAGE_PATH}" ]; then
  echo "Lambda 패키지를 찾을 수 없습니다: ${PACKAGE_PATH}" >&2
  echo "먼저 ./scripts/build-lambda-package.sh 를 실행하세요." >&2
  exit 1
fi

echo "[0/3] Lambda 함수 존재 여부 확인..."
if ! aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" lambda get-function --function-name "${FUNCTION_NAME}" >/dev/null 2>&1; then
  echo "함수가 없어 새로 생성합니다: ${FUNCTION_NAME}"
  ROLE_ARN=$(aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" iam get-role --role-name voj-lambda-api-role --query 'Role.Arn' --output text)
  if [ -z "${ROLE_ARN}" ]; then
    echo "IAM 역할 voj-lambda-api-role 을 찾을 수 없습니다. 먼저 scripts/create-lambda-roles.sh 실행 필요." >&2
    exit 1
  fi
  aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" \
    lambda create-function \
    --function-name "${FUNCTION_NAME}" \
    --runtime python3.12 \
    --role "${ROLE_ARN}" \
    --handler backend.app.handler.handler \
    --timeout 30 \
    --memory-size 512 \
    --zip-file "fileb://${PACKAGE_PATH}" >/dev/null
fi

echo "[1/3] Lambda 코드 업로드 중..."
aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" \
  lambda update-function-code \
  --function-name "${FUNCTION_NAME}" \
  --zip-file "fileb://${PACKAGE_PATH}" >/dev/null

if [ -f "${ENV_FILE}" ]; then
  echo "[2/3] 환경 변수 동기화 (${ENV_FILE})"
  ENV_JSON=$(python3 - "$ENV_FILE" <<'PY'
import json, sys
from pathlib import Path

RESERVED_PREFIXES = ("AWS_", "LAMBDA_")

def load_env(path: Path):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        # Filter reserved keys (Lambda-managed)
        if key.startswith(RESERVED_PREFIXES):
            continue
        env[key] = value
    return env

env_file = Path(sys.argv[1])
if not env_file.exists():
    print('{}')
    sys.exit(0)
print(json.dumps({"Variables": load_env(env_file)}))
PY
)
  if [ "${ENV_JSON}" != "{}" ]; then
    # 직전 코드 업데이트 이후 구성이 잠길 수 있어 대기
    for i in 1 2 3 4 5; do
      echo "구성 업데이트 시도($i)..." >&2
      set +e
      aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" \
        lambda update-function-configuration \
        --function-name "${FUNCTION_NAME}" \
        --environment "${ENV_JSON}" >/dev/null
      rc=$?
      set -e
      if [ $rc -eq 0 ]; then
        break
      fi
      sleep 5
    done
    if [ $rc -ne 0 ]; then
      echo "환경 변수 업데이트 실패(잠김 지속)" >&2
    fi
  fi
else
  echo "환경 파일(${ENV_FILE}) 이 없어 Lambda 환경 변수는 건너뜁니다."
fi

# Handler 보정 (옵션): HANDLER_NAME 환경변수 또는 기본값 적용
HANDLER_NAME="${HANDLER_NAME:-$HANDLER_NAME_DEFAULT}"
echo "[2b] Lambda 핸들러 설정: ${HANDLER_NAME}"
aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" \
  lambda update-function-configuration \
  --function-name "${FUNCTION_NAME}" \
  --handler "${HANDLER_NAME}" >/dev/null

if [ -n "${API_ID}" ]; then
  echo "[3/3] API Gateway Stage 재배포 (${API_STAGE})"
  DEPLOYMENT_ID=$(aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" \
    apigatewayv2 create-deployment \
    --api-id "${API_ID}" \
    --query 'DeploymentId' --output text)
  aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" \
    apigatewayv2 update-stage \
    --api-id "${API_ID}" \
    --stage-name "${API_STAGE}" \
    --deployment-id "${DEPLOYMENT_ID}" >/dev/null
else
  echo "API Gateway ID가 지정되지 않아 Stage 재배포는 생략합니다."
fi

echo "배포 스크립트 완료."
