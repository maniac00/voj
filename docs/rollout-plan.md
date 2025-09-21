# 프로덕션 롤아웃 플랜 (ECR/ECS/ALB)

ECS 전환에 맞춘 단계별 배포/전환/롤백 절차입니다.

## 1. 사전 검증

- [ ] 로컬/스테이징 통합 테스트 (`poetry run pytest`, `npm run build`)
- [ ] 컨테이너 헬스 체크 `/api/v1/health` 200 확인(로컬 도커)
- [ ] SSM/Secrets 값 점검(필수 키 존재)

## 2. 백엔드 배포 (ECR→ECS)

1. Docker 이미지 빌드/푸시(ECR)
2. ECS Task Definition 신규 리비전 등록
3. ECS Service 업데이트(롤링)
4. ALB TargetGroup 헬스 100% 달성 확인

## 3. 도메인 전환

- Route53: `api.voj-audiobook.com` A-ALIAS → 새 ALB로 스위치(필요 시 weighted 전환)
- HTTPS/헤더/CORS 검증(프론트와 통신)

## 4. 단계적 공개(옵션)

- [ ] Weighted Routing으로 10% → 50% → 100%
- [ ] 24시간 모니터링 후 완전 전환

## 5. 모니터링

- CloudWatch: 4xx/5xx, p95 latency, CPU/Mem, Target Unhealthy 수
- 로그: `/ecs/voj-backend` 스트림에서 앱 에러 확인

## 6. 롤백

- ECS 서비스에 이전 태스크 정의 리비전으로 재배포
- Route53 가중치 0%로 원복

## 7. 클린업

- 불필요 리소스 정리: Lambda, API Gateway, Function URL, 관련 IAM 정책/스크립트
- 문서/레포에서 구 경로 삭제 및 링크 업데이트
