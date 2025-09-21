#!/bin/bash
# DEPRECATED: Lambda 배포 경로는 ECR/ECS/ALB로 전환되었습니다. 유지보수 중단.
set -euo pipefail

# Build Lambda ZIP on host (macOS) with Linux-compatible wheels via pip download
# Output: dist/backend_lambda.zip

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/.lambda-build-host"
WHEEL_DIR="${BUILD_DIR}/wheels"
PACKAGE_DIR="${BUILD_DIR}/package"
DIST_DIR="${REPO_ROOT}/dist"

rm -rf "${BUILD_DIR}" && mkdir -p "${WHEEL_DIR}" "${PACKAGE_DIR}" "${DIST_DIR}"

# Ensure Poetry + export plugin
python3 -m pip install --user "poetry==1.8.3" >/dev/null 2>&1 || true
python3 -m poetry self add poetry-plugin-export@^1.8.0 >/dev/null 2>&1 || true

# Make sure lock matches pyproject (ensures deps like mangum are in export)
python3 -m poetry lock --no-update >/dev/null 2>&1 || true

# Export requirements
REQ_FILE="${BUILD_DIR}/requirements.txt"
python3 -m poetry export -f requirements.txt --output "${REQ_FILE}" --without-hashes

# Download manylinux wheels for Python 3.12 cp312 x86_64 only (no builds)
PYVER=3.12
pip download \
  --requirement "${REQ_FILE}" \
  --dest "${WHEEL_DIR}" \
  --only-binary=:all: \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version ${PYVER/./} \
  --abi cp312

# Unpack wheels into package directory (pass args before heredoc)
python3 - "${WHEEL_DIR}" "${PACKAGE_DIR}" <<'PY'
import sys, zipfile
from pathlib import Path
wheels_dir = Path(sys.argv[1])
target = Path(sys.argv[2])
target.mkdir(parents=True, exist_ok=True)
for whl in wheels_dir.glob('*.whl'):
    with zipfile.ZipFile(whl) as zf:
        zf.extractall(target)
print('Unpacked wheels to', target)
PY

# Copy application code so that backend/ is at the zip root to match handler path
rsync -a \
  --exclude '/tests/' \
  --exclude '/docs/' \
  --exclude '/storage/' \
  --exclude '/tmp_test_media/' \
  --exclude '__pycache__' \
  "${REPO_ROOT}/backend/" "${PACKAGE_DIR}/backend/"

# Zip package
pushd "${PACKAGE_DIR}" >/dev/null
zip -rq "${DIST_DIR}/backend_lambda.zip" .
popd >/dev/null

echo "Created Lambda package at ${DIST_DIR}/backend_lambda.zip"


