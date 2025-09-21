# 프로덕션 모니터링 가이드

## 1. 개요

VOJ Audiobooks 프로덕션 환경에서 Lambda, API Gateway, CloudFront, S3의 주요 지표를 추적하고 알람을 설정하는 방법을 정리했습니다. 배포 체크리스트 10.x 단계 수행 시 참고하세요.

## 2. 공통 전제

- AWS 리전: `ap-northeast-2`
- 지표/알람은 기본적으로 CloudWatch에 저장
- Slack 혹은 이메일 알림을 위해 SNS Topic을 준비 (`voj-prod-alarms` 등)

## 3. Lambda 모니터링 (10.1)

### 필수 지표

| 지표 | 네임스페이스 | 기준 | 설명 |
| --- | --- | --- | --- |
| `Errors` | `AWS/Lambda` | `Sum` | 에러 횟수 증가 감지 |
| `Duration` | `AWS/Lambda` | `p95` | 95퍼센타일 실행 시간 모니터링 |
| `Throttles` | `AWS/Lambda` | `Sum` | 동시 실행 제한으로 인한 실패 |

### 알람 예시

- `Errors` ≥ 3 (5분) → SNS 알림
- `Duration` ≥ 25초 (5분) → 성능 문제 알림
- `Throttles` ≥ 1 (5분) → 동시성 조정 필요

## 4. API Gateway 모니터링 (10.2)

### 필수 지표

| 지표 | 네임스페이스 | 기준 |
| --- | --- | --- |
| `5XXError` | `AWS/ApiGateway` | `Sum` |
| `4XXError` | `AWS/ApiGateway` | `Sum` |
| `Latency` | `AWS/ApiGateway` | `Average` |

### 알람 기준

- `5XXError` ≥ 5 (5분)
- `4XXError` 비율 급증 시 탐지: `4XXError / Count * 100` ≥ 20%
- `Latency` ≥ 5초 (p95)

## 5. CloudFront 모니터링 (10.3)

### 지표

| 지표 | 네임스페이스 | 기준 |
| --- | --- | --- |
| `5xxErrorRate` | `AWS/CloudFront` | `Average` |
| `TotalErrorRate` | `AWS/CloudFront` | `Average` |
| `BytesDownloaded` | `AWS/CloudFront` | `Sum` |

### 알람 예시

- `5xxErrorRate` ≥ 1% (5분)
- `TotalErrorRate` ≥ 5% (5분)

> CloudFront 지표는 `Region` 대신 `Global`을 선택해야 합니다.

## 6. S3 접근 모니터링 (10.4)

- S3 서버 액세스 로그를 CloudWatch Logs 또는 Athena로 전송
- 지표 필터 예시: `status=403` 요청 증가 감시
- CloudWatch Metrics Insights를 이용해 `403` 비율을 집계하고 알람으로 연동

## 7. 로그 보존 및 비용 최적화 (10.5)

- CloudWatch Logs 그룹 보존 기간: 기본 30일 설정 (필요 시 90일)
- S3 로그 버킷에 Lifecycle Rule 적용 (예: 90일 후 Glacier Deep Archive)
- AWS Budgets로 월별 로그 비용 경보 설정

## 8. CloudWatch 대시보드 템플릿

아래 JSON 샘플을 참고해 CloudWatch 대시보드를 생성할 수 있습니다.

```json
{
  "widgets": [
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Errors", "FunctionName", "voj-backend-api"],
          ["AWS/Lambda", "Throttles", "FunctionName", "voj-backend-api"],
          ["AWS/Lambda", "Duration", "FunctionName", "voj-backend-api", {"stat": "p95"}]
        ],
        "title": "Lambda Health",
        "region": "ap-northeast-2",
        "view": "timeSeries",
        "stacked": false
      }
    }
  ]
}
```

## 9. 참고 자료

- CloudWatch 알람 CLI: <https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/put-metric-alarm.html>
- Lambda 모범사례: <https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html>
- CloudFront 지표: <https://docs.aws.amazon.com/amazoncloudfront/latest/DeveloperGuide/monitoring-using-cloudwatch.html>
