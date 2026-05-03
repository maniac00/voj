# Railway 마이그레이션 실행 가이드

Railway CLI의 서비스 선택 제약으로 인해 로컬에서 DATABASE_URL을 사용하여 마이그레이션을 실행합니다.

## 방법 1: Railway 대시보드에서 DATABASE_URL 복사 (권장)

### 1단계: DATABASE_URL 복사

1. **Railway 대시보드 접속**
   ```
   https://railway.com/project/ca0cd363-66b4-41f5-bbcb-b2c49ce7ba29
   ```

2. **PostgreSQL 서비스 클릭**
   - 좌측 사이드바에서 "Postgres" 또는 "PostgreSQL" 서비스 선택

3. **Variables 탭 클릭**

4. **DATABASE_URL 복사**
   - `DATABASE_URL` 값 우측의 복사 아이콘 클릭
   - 형식: `postgresql://user:pass@host:port/database`

### 2단계: 로컬에서 마이그레이션 실행

```bash
# DATABASE_URL 설정 (복사한 값 붙여넣기)
export DATABASE_URL='postgresql://postgres:...'

# 마이그레이션 실행
cd backend
alembic upgrade head
```

**또는 스크립트 사용:**

```bash
export DATABASE_URL='복사한_URL'
./scripts/railway-migrate.sh
```

---

## 방법 2: Railway One-Off Command (대시보드)

### 단계:

1. **백엔드 서비스 클릭**

2. **Settings** 탭

3. **"Deploy"** 섹션

4. **"One-off Command"** 입력:
   ```bash
   alembic upgrade head
   ```

5. **"Run"** 클릭

### 로그 확인:
- Deployments 탭에서 실행 로그 확인

---

## 방법 3: Dockerfile에 마이그레이션 추가 (자동화)

### backend/Dockerfile 수정:

Dockerfile의 CMD 전에 마이그레이션 추가:

```dockerfile
# 기존 CMD 주석 처리
# CMD ["sh", "-c", "/opt/venv/bin/gunicorn ..."]

# 새로운 시작 스크립트 사용
COPY --from=builder /app/scripts/start.sh /app/start.sh
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
```

### backend/scripts/start.sh 생성:

```bash
#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec /opt/venv/bin/gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:${PORT:-8000} \
  --workers ${GUNICORN_WORKERS:-2} \
  --timeout ${GUNICORN_TIMEOUT:-60}
```

---

## 🔍 마이그레이션 확인

### 테이블 생성 확인:

```bash
# psql 사용 (psql 설치 필요)
psql $DATABASE_URL -c '\dt'

# 또는 Python으로 확인
python -c "
from sqlalchemy import create_engine, inspect
import os
engine = create_engine(os.getenv('DATABASE_URL'))
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', tables)
"
```

### 예상 테이블:
- ✅ `books`
- ✅ `audio_chapters`
- ✅ `alembic_version`

---

## ❌ 문제 해결

### "psycopg2 not installed"

```bash
# psycopg2-binary 설치 확인
poetry show psycopg2-binary

# 없으면 설치
poetry add psycopg2-binary
```

### "postgres:// URL 형식" 오류

Railway는 `postgres://`를 사용하지만 SQLAlchemy는 `postgresql://` 필요:

```bash
# URL 수정
export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"
```

스크립트는 자동으로 처리합니다.

### "No such file or directory: alembic"

```bash
# backend 디렉토리에서 실행 확인
cd backend
alembic upgrade head
```

### "Target database is not up to date"

```bash
# 현재 버전 확인
alembic current

# 강제 stamp
alembic stamp head

# 다시 실행
alembic upgrade head
```

---

## ✅ 성공 확인

마이그레이션 성공 시 출력:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial, Initial migration - Create books and audio_chapters tables
```

테이블 확인:

```bash
psql $DATABASE_URL -c '\dt'

# 출력:
#           List of relations
#  Schema |      Name       | Type  |  Owner
# --------+-----------------+-------+----------
#  public | alembic_version | table | postgres
#  public | audio_chapters  | table | postgres
#  public | books           | table | postgres
```

---

## 🎯 다음 단계

마이그레이션 완료 후:

1. **백엔드 배포 확인**
   ```bash
   curl https://your-backend.railway.app/health
   ```

2. **API 테스트**
   ```bash
   curl https://your-backend.railway.app/api/v1/health
   ```

3. **프론트엔드 배포**
   ```bash
   cd frontend
   vercel
   ```
