#!/bin/bash
# DEPRECATED: Lambda 배포 경로는 ECR/ECS/ALB로 전환되었습니다. 유지보수 중단.
set -euo pipefail

# Builds backend Lambda deployment zip into dist/backend_lambda.zip

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/.lambda-build"
PACKAGE_DIR="${BUILD_DIR}/package"
DIST_DIR="${REPO_ROOT}/dist"

rm -rf "${BUILD_DIR}"
mkdir -p "${PACKAGE_DIR}" "${DIST_DIR}"

REQ_FILE="${BUILD_DIR}/requirements.txt"
if ! poetry export -f requirements.txt --output "${REQ_FILE}" --without-hashes >/dev/null 2>&1; then
  echo "Poetry export plugin not found. Run: poetry self add poetry-plugin-export" >&2
  exit 1
fi

python3 -m pip install --no-cache-dir -r "${REQ_FILE}" --target "${PACKAGE_DIR}" >/dev/null

rsync -a \
  --exclude 'tests/' \
  --exclude 'docs/' \
  --exclude 'storage/' \
  --exclude 'tmp_test_media/' \
  --exclude '__pycache__' \
  "${REPO_ROOT}/backend/" "${PACKAGE_DIR}/backend/"

pushd "${PACKAGE_DIR}" >/dev/null
zip -rq "${DIST_DIR}/backend_lambda.zip" .
popd >/dev/null

echo "Created Lambda package at ${DIST_DIR}/backend_lambda.zip"
