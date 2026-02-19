# Telegram 관리자 알림 설정 가이드

신규 사용자가 앱에 가입하면 Telegram으로 알림이 오고, 버튼 클릭으로 승인/거부를 처리할 수 있습니다.

---

## 1단계: 내 Chat ID 확인

1. Telegram에서 **@userinfobot** 검색
2. 채팅 시작 후 아무 메시지나 전송
3. 응답에서 `Your user ID` 값을 메모

```
Your user ID: 123456789
```

이 숫자가 본인의 **Chat ID**입니다. 관리자 설정에 필요하니 따로 메모해두세요.

---

## 2단계: VOJ Bot과 대화 시작

1. Telegram에서 VOJ 관리자 Bot을 검색 (Bot 이름은 담당자에게 문의)
2. `/start` 전송

> 이 단계를 건너뛰면 Bot이 메시지를 보낼 수 없습니다.

---

## 3단계: 담당자에게 Chat ID 전달

확인한 Chat ID를 담당자에게 전달하면 Railway 환경변수에 등록됩니다.
등록 완료 후 신규 사용자 가입 시 알림이 수신됩니다.

---

## 승인/거부 사용 방법

### 알림 메시지 예시

```
🔔 신규 사용자 가입 요청

ID: 5
이메일: newuser@gmail.com
이름: 홍길동

승인 또는 거부를 선택해주세요.
[✅ 승인]  [❌ 거부]
```

### 버튼 클릭 흐름

**승인하는 경우:**
1. `[✅ 승인]` 클릭
2. 확인 메시지 표시 → `[✓ 확인]` 클릭
3. "✅ 승인 완료" 메시지로 변경됨

**거부하는 경우:**
1. `[❌ 거부]` 클릭
2. 확인 메시지 표시 → `[✓ 확인]` 클릭
3. "❌ 거부 완료" 메시지로 변경됨

**실수로 클릭했을 때:**
- `[✗ 취소]` 클릭 → 원래 승인/거부 버튼으로 돌아감

> 두 관리자 중 한 명이 먼저 처리하면, 나머지 한 명이 버튼을 클릭해도 "이미 처리된 사용자입니다"라고 표시됩니다.

---

## (담당자용) 초기 설정

처음 한 번만 진행하는 설정입니다.

### Bot 생성

1. Telegram에서 **@BotFather** 검색
2. `/newbot` 입력
3. Bot 이름 입력 (예: `VOJ 관리자`)
4. Bot 사용자명 입력 — 반드시 `bot`으로 끝나야 함 (예: `voj_admin_bot`)
5. 발급된 **Bot Token** 메모

```
7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Webhook Secret 생성

터미널에서 임의의 문자열 생성:

```bash
openssl rand -hex 32
```

### Railway 환경변수 등록

Railway 대시보드 → `voj-production` 서비스 → **Variables** 탭에서 추가:

| Key | Value |
|-----|-------|
| `TELEGRAM_BOT_TOKEN` | BotFather에서 발급받은 토큰 |
| `TELEGRAM_ADMIN_CHAT_IDS` | 관리자 Chat ID 2개를 콤마로 구분 (예: `123456789,987654321`) |
| `TELEGRAM_WEBHOOK_SECRET` | openssl로 생성한 문자열 |

설정 후 Railway가 자동 재배포합니다.

### Webhook 등록 (재배포 완료 후 1회 실행)

```bash
curl -X POST "https://api.telegram.org/bot{TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://voj-production.up.railway.app/api/v1/telegram/webhook",
    "secret_token": "{SECRET}"
  }'
```

성공 응답:

```json
{"ok": true, "result": true, "description": "Webhook was set"}
```

### 등록 확인

```bash
curl "https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
```

`url` 필드가 올바르게 표시되면 설정 완료입니다.