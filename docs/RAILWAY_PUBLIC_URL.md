# Railway Public Database URL 가져오기

## ⚠️ 문제
`postgres.railway.internal`은 Railway 내부 네트워크 주소로, 로컬에서 접근할 수 없습니다.

## ✅ 해결: Public URL 사용

### 방법 1: Railway 대시보드에서 Public URL 복사

1. **PostgreSQL 서비스 클릭**
   - https://railway.com/project/ca0cd363-66b4-41f5-bbcb-b2c49ce7ba29

2. **Connect 탭 클릭** (또는 Variables 탭)

3. **Public Network 섹션에서 복사**
   - "Postgres Connection URL (Public)" 또는
   - "DATABASE_PUBLIC_URL" 또는
   - TCP Proxy 주소 사용

4. **형식:**
   ```
   postgresql://postgres:PASSWORD@monorail.proxy.rlwy.net:PORT/railway
   ```

### 방법 2: Railway CLI로 가져오기

Railway 서비스에서 직접 실행:

```bash
# Railway에서 마이그레이션 실행
railway run -s [서비스명] alembic upgrade head
```

### 방법 3: Railway 대시보드에서 직접 실행 (권장)

1. **백엔드 서비스 클릭**
2. **Settings** → **Deploy**
3. **One-off Command** 입력:
   ```bash
   alembic upgrade head
   ```
4. **Run** 클릭

---

## 🔍 Public URL 찾는 법

### Connect 탭에서:
- "Postgres Connection URL" 섹션
- Host가 `monorail.proxy.rlwy.net` 또는 `containers.pkg.dev` 형식

### Variables 탭에서:
- `DATABASE_PUBLIC_URL` 찾기
- 또는 `PGHOST`, `PGPORT` 조합하여 URL 생성

### 예시:
```bash
# Internal (로컬 접근 불가) ❌
postgres.railway.internal:5432

# Public (로컬 접근 가능) ✅
monorail.proxy.rlwy.net:12345
```

---

## 🚀 마이그레이션 실행

### Public URL 확인 후:

```bash
# Public URL 사용
export DATABASE_URL='postgresql://postgres:PASSWORD@monorail.proxy.rlwy.net:PORT/railway'

# 마이그레이션 실행
cd backend
poetry run alembic upgrade head
```

---

## 💡 가장 쉬운 방법

**Railway 대시보드에서 One-off Command 실행:**

1. 백엔드 서비스 → Settings → Deploy
2. One-off Command: `alembic upgrade head`
3. Run 클릭

이 방법은 Railway 내부 네트워크를 사용하므로 Public URL 불필요!
