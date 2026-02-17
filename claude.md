# Cloudflare Infrastructure Rules

> ⚠️ 이 문서는 Claude Code가 Cloudflare 설정 시 반드시 따라야 할 최신 규칙입니다.
> 학습 데이터에 있는 오래된 패턴을 사용하지 마세요.

## 설정 파일 포맷

- **반드시 `wrangler.jsonc`를 사용할 것** (`wrangler.toml` 사용 금지)
- Cloudflare 공식 권장 포맷은 wrangler v3.91.0+ 기준 `wrangler.jsonc`임
- `$schema`를 반드시 포함: `"$schema": "node_modules/wrangler/config-schema.json"`
- `compatibility_date`는 `"2025-01-01"` 이상으로 설정
- `compatibility_flags`에 `"nodejs_compat"` 포함

### wrangler.jsonc 기본 템플릿

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "my-worker",
  "main": "src/index.ts",
  "compatibility_date": "2025-01-01",
  "compatibility_flags": ["nodejs_compat"],
  "r2_buckets": [
    {
      "binding": "MY_BUCKET",
      "bucket_name": "my-bucket-name"
    }
  ]
}
```

## R2 설정 규칙

### 자동 프로비저닝 (wrangler v4.45.0+)
- R2 버킷을 수동으로 먼저 생성할 필요 없음
- `wrangler.jsonc`에 바인딩만 추가하면 `wrangler deploy` 시 자동 생성됨
- `bucket_name` 없이 binding만 넣으면 worker 이름을 prefix로 자동 생성
- ❌ 더 이상 `wrangler r2 bucket create <name>`을 별도로 실행하지 않아도 됨
- 자동 프로비저닝 비활성화: `--no-x-provision` 플래그

### R2 바인딩 설정
```jsonc
{
  "r2_buckets": [
    {
      "binding": "MY_BUCKET",        // Worker 코드에서 사용할 변수명
      "bucket_name": "my-bucket",     // 실제 R2 버킷 이름
      "preview_bucket_name": "my-bucket-preview"  // (선택) wrangler dev --remote 시 사용
    }
  ]
}
```

### R2 Worker 코드 패턴 (Module Worker 문법만 사용)
```typescript
// ✅ 올바른 패턴: Module Worker (ES Modules)
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const object = await env.MY_BUCKET.get("my-key");
    // ...
  }
} satisfies ExportedHandler<Env>;

interface Env {
  MY_BUCKET: R2Bucket;
}
```

```javascript
// ❌ 금지: Service Worker (addEventListener) 문법 사용하지 말 것
addEventListener('fetch', event => { ... })
```

### R2 로컬 개발
- `wrangler dev`는 기본적으로 로컬 스토리지에 R2 데이터를 저장함
- 원격 R2 버킷 사용하려면: 바인딩에 `"remote": true` 설정

## Cloudflare Pages 관련

- ❌ Cloudflare Pages는 2025년 4월 deprecated됨
- ✅ 정적 사이트도 Workers를 사용할 것
- `pages_build_output_dir` 속성으로 정적 파일 디렉토리 지정

## 배포 명령어

```bash
# 개발
npx wrangler dev

# 배포
npx wrangler deploy

# ❌ 사용 금지 (deprecated)
# wrangler pages publish
# wrangler publish
```

## 프로젝트 생성

```bash
# 새 프로젝트 생성 시 create-cloudflare CLI 사용
npm create cloudflare@latest

# ❌ wrangler init은 레거시
```

## 중요 참고사항

- 확실하지 않은 Cloudflare 설정이 있으면, 반드시 공식 문서를 웹 검색해서 확인할 것
- 공식 문서: https://developers.cloudflare.com/r2/
- Wrangler 설정 문서: https://developers.cloudflare.com/workers/wrangler/configuration/
