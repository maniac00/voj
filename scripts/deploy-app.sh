#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

API_BASE_URL="https://voj-production.up.railway.app/api/v1"
R2_BUCKET="voj-releases"
R2_PUBLIC_URL="https://voj-releases.7wario.workers.dev"

# --- 1. 버전 읽기 ---
PUBSPEC="$PROJECT_ROOT/mobile/pubspec.yaml"
VERSION_LINE=$(grep '^version:' "$PUBSPEC" | head -1)
FULL_VERSION=$(echo "$VERSION_LINE" | awk '{print $2}')
VERSION=$(echo "$FULL_VERSION" | cut -d'+' -f1)
BUILD_NUMBER=$(echo "$FULL_VERSION" | cut -d'+' -f2)

echo "=== 모바일 앱 배포 ==="
echo "버전: $VERSION (build $BUILD_NUMBER)"
echo ""

# --- 2. Flutter APK 빌드 ---
echo "[1/6] APK 빌드 중..."
cd "$PROJECT_ROOT/mobile"
flutter build apk --release \
  --dart-define=VOJ_API_BASE_URL="$API_BASE_URL"

APK_PATH="$PROJECT_ROOT/mobile/build/app/outputs/flutter-apk/app-release.apk"

if [[ ! -f "$APK_PATH" ]]; then
  echo "ERROR: APK 파일을 찾을 수 없습니다: $APK_PATH"
  exit 1
fi

# --- 3. 파일 크기 확인 ---
FILE_SIZE=$(stat -f%z "$APK_PATH" 2>/dev/null || stat -c%s "$APK_PATH")
FILE_SIZE_MB=$(echo "scale=1; $FILE_SIZE / 1048576" | bc)
echo "APK 크기: ${FILE_SIZE_MB}MB ($FILE_SIZE bytes)"
echo ""

# --- 4. R2 업로드 (버전별 APK만) ---
APK_NAME="voice-of-juan-v${VERSION}.apk"
R2_KEY="android/$APK_NAME"

echo "[2/6] R2에 APK 업로드 중..."
cd "$PROJECT_ROOT/r2-worker"
npx wrangler r2 object put "$R2_BUCKET/$R2_KEY" --file="$APK_PATH" --remote
echo "업로드 완료: $R2_KEY"
echo ""

# --- 5. metadata.json 업데이트 ---
echo "[3/6] metadata.json 업데이트 중..."
METADATA_PATH="$PROJECT_ROOT/download-page/public/metadata.json"
RELEASE_DATE=$(date +%Y-%m-%d)
DOWNLOAD_URL="$R2_PUBLIC_URL/$R2_KEY"

cat > "$METADATA_PATH" << EOF
{
  "android": {
    "latestVersion": "$VERSION",
    "latestBuildNumber": $BUILD_NUMBER,
    "downloadUrl": "$DOWNLOAD_URL",
    "fileSize": $FILE_SIZE,
    "releaseDate": "$RELEASE_DATE",
    "changelog": "v$VERSION 릴리스"
  }
}
EOF

echo "metadata.json 업데이트 완료"
echo ""

# --- 6. 다운로드 페이지 배포 ---
echo "[4/6] 다운로드 페이지 배포 중..."
cd "$PROJECT_ROOT/download-page"
npx wrangler deploy
echo ""

# --- 7. 변경된 파일 커밋 & 푸시 ---
echo "[5/6] 버전 및 metadata 커밋 & 푸시 중..."
cd "$PROJECT_ROOT"
git add mobile/pubspec.yaml download-page/public/metadata.json
git commit -m "chore: release v${VERSION}+${BUILD_NUMBER}" || true
git push origin HEAD

# --- 8. 완료 요약 ---
echo ""
echo "[6/6] 배포 완료!"
echo ""
echo "=============================="
echo "  배포 요약"
echo "=============================="
echo "  버전:     $VERSION+$BUILD_NUMBER"
echo "  APK 크기: ${FILE_SIZE_MB}MB"
echo "  R2 경로:  $R2_KEY"
echo "  다운로드:  $DOWNLOAD_URL"
echo "  페이지:   https://voj-download.7wario.workers.dev"
echo "=============================="
