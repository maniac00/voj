# VOJ Backend Infra (CDK)

구성 리소스(초안):
- VPC(2AZ, Public+Private)
- ALB(HTTPS, ACM 인증서)
- ECS Cluster + Fargate Service(Task: container: backend)
- CloudWatch Logs 그룹(`/ecs/voj-backend`)
- Route53 A-ALIAS `api.voj-audiobook.com` → ALB

필요 매개변수:
- hostedZoneId / hostedZoneName
- certificateArn (없으면 CDK로 DNS 검증 발급 가능)
- ecrRepoName (기본: `voj-backend`)

명령:
```bash
cd infra/cdk
npm ci
npx cdk synth
npx cdk deploy --all --require-approval never
```


