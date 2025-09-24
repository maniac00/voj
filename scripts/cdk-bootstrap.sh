#!/bin/bash
set -euo pipefail

# CDK bootstrap for VOJ infra (ECS/ALB)
# Usage:
#   AWS_PROFILE=admin AWS_REGION=ap-northeast-2 ./scripts/cdk-bootstrap.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

REGION="${AWS_REGION:-ap-northeast-2}"

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI is required" >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required" >&2
  exit 1
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
if [[ -z "${ACCOUNT_ID}" || "${ACCOUNT_ID}" == "null" ]]; then
  echo "Failed to resolve AWS Account ID (check your credentials)" >&2
  exit 1
fi

cd "${REPO_ROOT}/infra/cdk"

if [[ ! -d node_modules ]]; then
  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi
fi

echo "Bootstrapping CDK for ${ACCOUNT_ID}/${REGION}..."
npx cdk bootstrap "aws://${ACCOUNT_ID}/${REGION}"
echo "✅ CDK bootstrap completed"


