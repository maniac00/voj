#!/bin/bash
set -euo pipefail

# CDK deploy for VOJ infra (ECS/ALB)
# Usage:
#   AWS_PROFILE=admin AWS_REGION=ap-northeast-2 \
#   HOSTED_ZONE_NAME=voj-audiobook.com DOMAIN_NAME=api.voj-audiobook.com \
#   ECR_REPO=voj-backend ./scripts/cdk-deploy.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

REGION="${AWS_REGION:-ap-northeast-2}"
HOSTED_ZONE_NAME="${HOSTED_ZONE_NAME:-voj-audiobook.com}"
DOMAIN_NAME="${DOMAIN_NAME:-api.voj-audiobook.com}"
ECR_REPO="${ECR_REPO:-voj-backend}"

cd "${REPO_ROOT}/infra/cdk"

if [[ ! -d node_modules ]]; then
  npm ci
fi

echo "Synthesizing CDK app..."
npx cdk synth -c hostedZoneName="${HOSTED_ZONE_NAME}" -c domainName="${DOMAIN_NAME}" -c ecrRepo="${ECR_REPO}" >/dev/null

echo "Deploying CDK stacks..."
npx cdk deploy --all --require-approval never \
  -c hostedZoneName="${HOSTED_ZONE_NAME}" \
  -c domainName="${DOMAIN_NAME}" \
  -c ecrRepo="${ECR_REPO}"

echo "✅ CDK deploy completed"


