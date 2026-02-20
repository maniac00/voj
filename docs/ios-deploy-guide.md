# iOS TestFlight 배포 가이드

앱 코드의 iOS 준비는 완료된 상태입니다. 아래 외부 설정 작업을 순서대로 진행하세요.

---

## 1단계: Apple Developer Program 가입

1. https://developer.apple.com/programs/ 접속
2. **Enroll** 클릭 → 개인(Individual) 또는 조직(Organization) 선택
3. 연회비 $99 결제
4. 승인까지 최대 2일 소요

---

## 2단계: Firebase Console에서 iOS 앱 추가

1. https://console.firebase.google.com 접속 → VOJ 프로젝트 선택
2. 프로젝트 설정 → **앱 추가** → iOS 선택
3. 아래 정보 입력:
   - **Bundle ID**: Apple Developer에서 등록한 Bundle ID와 동일하게 입력
   - **앱 닉네임**: 주안의 소리 iOS
4. `GoogleService-Info.plist` 다운로드
5. 다운로드한 파일을 아래 경로에 저장:
   ```
   mobile/ios/Runner/GoogleService-Info.plist
   ```
6. Xcode에서 파일 추가 확인:
   - `mobile/ios/Runner.xcworkspace` 열기
   - Runner 타겟에 `GoogleService-Info.plist`가 포함되어 있는지 확인

---

## 3단계: Xcode에서 Bundle ID 및 팀 설정

1. `mobile/ios/Runner.xcworkspace` 열기
2. 좌측 파일 트리에서 **Runner** 선택 → **Signing & Capabilities** 탭
3. **Team**: Apple Developer 계정 선택
4. **Bundle Identifier**: Firebase에서 등록한 Bundle ID와 동일하게 수정
   - 예: `com.voiceofjuan.app`
5. **Automatically manage signing** 체크

---

## 4단계: Google Sign-In URL Scheme 설정

> `GoogleService-Info.plist`의 `REVERSED_CLIENT_ID` 값이 필요합니다.

1. `GoogleService-Info.plist`를 열어 `REVERSED_CLIENT_ID` 값 복사
   - 예: `com.googleusercontent.apps.123456789-abcdefg`
2. `mobile/ios/Runner/Info.plist` 파일에 아래 항목 추가:

```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleTypeRole</key>
        <string>Editor</string>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>여기에 REVERSED_CLIENT_ID 값 입력</string>
        </array>
    </dict>
</array>
```

---

## 5단계: App Store Connect에서 앱 등록

1. https://appstoreconnect.apple.com 접속
2. **나의 앱** → **+** → **새로운 앱**
3. 아래 정보 입력:
   - **플랫폼**: iOS
   - **이름**: 주안의 소리
   - **번들 ID**: 3단계에서 설정한 Bundle ID 선택
   - **SKU**: `voice-of-juan-ios` (임의 문자열)
4. 앱 생성 완료

---

## 6단계: ExportOptions.plist 생성

`mobile/ios/ExportOptions.plist` 파일 생성:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store-connect</string>
    <key>teamID</key>
    <string>여기에 팀 ID 입력</string>
    <key>uploadBitcode</key>
    <false/>
    <key>uploadSymbols</key>
    <true/>
</dict>
</plist>
```

> 팀 ID 확인: https://developer.apple.com/account → Membership Details → Team ID

---

## 7단계: App Store Connect API 키 발급

`deploy-ios.sh` 스크립트가 TestFlight 업로드에 사용합니다.

1. https://appstoreconnect.apple.com/access/integrations/api 접속
2. **+** 클릭 → 키 이름: `VOJ Deploy`, 역할: `App Manager`
3. **다운로드** (한 번만 가능 — 안전한 곳에 보관)
4. 아래 값을 메모:
   - **Issuer ID** (페이지 상단)
   - **Key ID** (키 목록의 키 ID)
   - 다운로드한 `.p8` 파일 경로

5. 환경변수 설정 (배포 전 터미널에서 실행):
   ```bash
   export APP_STORE_CONNECT_API_KEY_ID="KEY_ID"
   export APP_STORE_CONNECT_ISSUER_ID="ISSUER_ID"
   ```

   또는 `~/.zshrc`에 영구 등록:
   ```bash
   echo 'export APP_STORE_CONNECT_API_KEY_ID="KEY_ID"' >> ~/.zshrc
   echo 'export APP_STORE_CONNECT_ISSUER_ID="ISSUER_ID"' >> ~/.zshrc
   ```

6. API 키 파일을 Xcode 기본 경로에 복사:
   ```bash
   mkdir -p ~/.appstoreconnect/private_keys
   cp AuthKey_KEYID.p8 ~/.appstoreconnect/private_keys/
   ```

---

## 8단계: iOS 배포 실행

모든 준비가 완료되면 배포 스크립트를 실행합니다.

```bash
bash scripts/deploy-ios.sh
```

처음 실행 시 Xcode에서 인증 관련 팝업이 뜰 수 있습니다. 허용해주세요.

---

## 9단계: TestFlight 내부 테스터 초대

1. App Store Connect → **주안의 소리** → **TestFlight** 탭
2. 빌드 처리 완료 후 (보통 10~30분)
3. **내부 테스트** → **+** → 테스터 이메일 추가
4. 테스터가 TestFlight 앱 설치 후 초대 이메일 링크로 설치

---

## 현재 완료된 기술적 준비 사항

- [x] iOS 폴더 및 Xcode 프로젝트 구성
- [x] 앱 아이콘 (모든 해상도)
- [x] 스플래시 화면
- [x] 백그라운드 오디오 재생 권한 (`UIBackgroundModes: audio`)
- [x] 배포 스크립트 (`scripts/deploy-ios.sh`)
- [ ] `GoogleService-Info.plist` (2단계 완료 후)
- [ ] Google Sign-In URL Scheme (4단계 완료 후)
- [ ] `ExportOptions.plist` (6단계 완료 후)
