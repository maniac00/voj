# Repository Guidelines

## Project Structure & Module Organization
- `backend/app` contains the FastAPI entrypoint plus `api/`, `services/`, and `models/`; manage migrations in `backend/alembic`.
- Root `tests/` holds audio, auth, and storage flows; isolate fixtures and clear `tmp_test_media/` after runs.
- `frontend/src` hosts the Next.js admin (`app/` routes, shared `components`, `hooks`, `lib`), with static assets in `frontend/public`.

## Build, Test, and Development Commands
- `./scripts/setup-local.sh` provisions Poetry, Node, and seeds `.env.local`; rerun whenever toolchains shift.
- `cd backend && poetry install && poetry run alembic upgrade head` readies the API; serve locally with `poetry run python -m app.main`.
- `cd frontend && npm install` then `npm run dev` launches the admin; `npm run build && npm start` simulates production.

## Coding Style & Naming Conventions
- Format Python with `poetry run black backend` and `poetry run isort backend`; respect 88-character lines and 4-space indents.
- Hold the line on typing via `poetry run mypy backend`; keep modules snake_case and services descriptive (`AudioTranscoderService`).
- Frontend code keeps components PascalCase, hooks camelCase, and must pass `npm run lint` and `npx prettier --check "src/**/*.{ts,tsx}"`.

## Testing Guidelines
- `poetry run pytest` (repo root) runs the backend suite configured for `tests/`; ensure `tmp_test_media/` is writable.
- Target files with `poetry run pytest tests/test_audio_upload_api.py`; colocate new fixtures beside the exercising test.
- Use `npm test` or `npm run test:watch` for frontend suites; capture regressions with `npm run test:coverage` and screenshots when visuals change.

## Commit & Pull Request Guidelines
- Write commits in the existing imperative voice ("Fix Dockerfile CMD shell substitution"); keep subjects under ~72 characters.
- Group changes by domain and reference issues in bodies using `Refs #123` when relevant.
- PRs should outline intent, affected endpoints or pages, and manual checks (`poetry run pytest`, `npm run lint`, `npm run type-check`); add UI diffs when visuals change and wait for green CI.

## Agent Communication
- 모든 에이전트 상태 업데이트, 리뷰 코멘트, 자동 응답은 반드시 한국어로 작성합니다; 영어 자료를 참고하더라도 결과는 한국어로 요약해 공유하세요.

## Environment & Deployment Notes
- Copy `env.local.example` or `env.production.example` when configuring secrets; never commit `.env*` files or `keys/` contents.
- Railway deploys via `railway.json` and the root `Dockerfile`; validate locally with `docker compose up --build` and sync infra edits in `infra/cdk`.
