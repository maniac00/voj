#!/usr/bin/env bash
# iOS IPA 빌드 및 TestFlight 업로드 스크립트
# 사전 준비 완료 후 실행: docs/ios-deploy-guide.md 참고
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- 버전 읽기 ---
PUBSPEC="$PROJECT_ROOT/mobile/pubspec.yaml"
VERSION_LINE=$(grep '^version:' "$PUBSPEC" | head -1)
FULL_VERSION=$(echo "$VERSION_LINE" | awk '{print $2}')
VERSION=$(echo "$FULL_VERSION" | cut -d'+' -f1)
BUILD_NUMBER=$(echo "$FULL_VERSION" | cut -d'+' -f2)

echo "=== iOS 앱 배포 ==="
echo "버전: $VERSION (build $BUILD_NUMBER)"
echo ""

# --- 사전 조건 확인 ---
echo "[준비] 사전 조건 확인 중..."

if ! command -v flutter &>/dev/null; then
  echo "ERROR: Flutter가 설치되어 있지 않습니다."
  exit 1
fi

if ! command -v xcrun &>/dev/null; then
  echo "ERROR: Xcode가 설치되어 있지 않습니다."
  exit 1
fi

IOS_DIR="$PROJECT_ROOT/mobile/ios"
if [[ ! -f "$IOS_DIR/Runner/GoogleService-Info.plist" ]]; then
  echo "ERROR: ios/Runner/GoogleService-Info.plist 파일이 없습니다."
  echo "       docs/ios-deploy-guide.md 의 2단계를 먼저 완료하세요."
  exit 1
fi

echo "사전 조건 확인 완료"
echo ""

# --- 1. Flutter pub get ---
echo "[1/5] 의존성 설치 중..."
cd "$PROJECT_ROOT/mobile"
flutter pub get
echo ""

# --- 2. IPA 빌드 ---
echo "[2/5] IPA 빌드 중..."
flutter build ipa --release \
  --dart-define=VOJ_API_BASE_URL="https://voj-production.up.railway.app/api/v1" \
  --export-options-plist="$IOS_DIR/ExportOptions.plist"

IPA_DIR="$PROJECT_ROOT/mobile/build/ios/ipa"
IPA_PATH=$(find "$IPA_DIR" -name "*.ipa" | head -1)

if [[ -z "$IPA_PATH" ]]; then
  echo "ERROR: IPA 파일을 찾을 수 없습니다."
  exit 1
fi

FILE_SIZE=$(stat -f%z "$IPA_PATH" 2>/dev/null || stat -c%s "$IPA_PATH")
FILE_SIZE_MB=$(echo "scale=1; $FILE_SIZE / 1048576" | bc)
echo "IPA 크기: ${FILE_SIZE_MB}MB"
echo ""

# --- 3. TestFlight 업로드 ---
echo "[3/5] TestFlight 업로드 중..."
xcrun altool \
  --upload-app \
  --type ios \
  --file "$IPA_PATH" \
  --apiKey "$APP_STORE_CONNECT_API_KEY_ID" \
  --apiIssuer "$APP_STORE_CONNECT_ISSUER_ID"

echo "TestFlight 업로드 완료"
echo ""

# --- 4. 버전 커밋 & 푸시 ---
echo "[4/5] 버전 커밋 & 푸시 중..."
cd "$PROJECT_ROOT"
git add mobile/pubspec.yaml
git commit -m "chore: release ios v${VERSION}+${BUILD_NUMBER}" || true
git push origin HEAD

# --- 5. 완료 ---
echo ""
echo "[5/5] 배포 완료!"
echo ""
echo "=============================="
echo "  iOS 배포 요약"
echo "=============================="
echo "  버전:     $VERSION+$BUILD_NUMBER"
echo "  IPA 크기: ${FILE_SIZE_MB}MB"
echo "  배포:     TestFlight"
echo "=============================="
echo ""
echo "App Store Connect에서 TestFlight 빌드 상태를 확인하세요:"
echo "  https://appstoreconnect.apple.com"
