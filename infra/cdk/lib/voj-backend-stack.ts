import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as certificatemanager from 'aws-cdk-lib/aws-certificatemanager';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as logs from 'aws-cdk-lib/aws-logs';

export class VojBackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Parameters / Context
    const domainName = this.node.tryGetContext('domainName');
    const hostedZoneName = this.node.tryGetContext('hostedZoneName');
    const hostedZoneId = this.node.tryGetContext('hostedZoneId');
    const ecrRepoName = this.node.tryGetContext('ecrRepo') || 'voj-backend';
    const s3BucketName = this.node.tryGetContext('s3BucketName') || 'voj-audiobooks-prod';
    const booksTableName = this.node.tryGetContext('booksTableName') || 'voj-books-prod';
    const audioChaptersTableName = this.node.tryGetContext('audioChaptersTableName') || 'voj-audio-chapters-prod';
    const corsOrigins = this.node.tryGetContext('corsOrigins') || 'https://voj-audiobooks.vercel.app';
    const enableDomainCtx = this.node.tryGetContext('enableDomain');
    const enableDomain = String(enableDomainCtx ?? 'false').toLowerCase() === 'true' && !!domainName && !!hostedZoneName;

    // VPC (2 AZ)
    const vpc = new ec2.Vpc(this, 'Vpc', {
      maxAzs: 2,
      natGateways: 1,
    });

    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'Cluster', { vpc });

    // ECR Repo (from name)
    const repo = ecr.Repository.fromRepositoryName(this, 'Repo', ecrRepoName);

    // Log group: reference existing '/ecs/voj-backend' to avoid AlreadyExists on redeploy
    const logGroup = logs.LogGroup.fromLogGroupName(this, 'Logs', '/ecs/voj-backend');

    // Certificate (DNS validated)
    let fargate: ecsPatterns.ApplicationLoadBalancedFargateService;
    if (enableDomain) {
      // Normalize CORS origins to JSON array string for container env
      const corsOriginsJson = (() => {
        try {
          const parsed = JSON.parse(String(corsOrigins));
          if (Array.isArray(parsed)) return JSON.stringify(parsed);
        } catch {}
        const arr = String(corsOrigins)
          .split(',')
          .map((s: string) => s.trim())
          .filter((s: string) => s.length > 0);
        return JSON.stringify(arr.length > 0 ? arr : ['https://voj-audiobooks.vercel.app']);
      })();
      const zone = hostedZoneId
        ? route53.HostedZone.fromHostedZoneAttributes(this, 'Zone', {
            hostedZoneId,
            zoneName: hostedZoneName!,
          })
        : route53.HostedZone.fromLookup(this, 'ZoneLookup', {
            domainName: hostedZoneName!,
          });

      const cert = new certificatemanager.DnsValidatedCertificate(this, 'Cert', {
        domainName: domainName!,
        hostedZone: zone,
        region: cdk.Stack.of(this).region,
      });

      fargate = new ecsPatterns.ApplicationLoadBalancedFargateService(this, 'Service', {
        cluster,
        cpu: 512,
        memoryLimitMiB: 1024,
        desiredCount: 2,
        publicLoadBalancer: true,
        certificate: cert,
        domainName: domainName!,
        domainZone: zone,
        redirectHTTP: true,
        listenerPort: 443,
        taskImageOptions: {
          image: ecs.ContainerImage.fromEcrRepository(repo),
          containerPort: 8000,
          logDriver: ecs.LogDrivers.awsLogs({ logGroup, streamPrefix: 'api' }),
        environment: {
          ENVIRONMENT: 'production',
          AWS_REGION: cdk.Stack.of(this).region,
          // Pydantic Settings expects JSON for list fields when sourced from env
          ALLOWED_HOSTS: '["*"]',
          S3_BUCKET_NAME: s3BucketName,
          BOOKS_TABLE_NAME: booksTableName,
          AUDIO_CHAPTERS_TABLE_NAME: audioChaptersTableName,
          CORS_ORIGINS: corsOriginsJson,
          RELEASE_ID: Date.now().toString(),
        },
        },
      });
    } else {
      // HTTP only (no domain)
      const corsOriginsJson = (() => {
        try {
          const parsed = JSON.parse(String(corsOrigins));
          if (Array.isArray(parsed)) return JSON.stringify(parsed);
        } catch {}
        const arr = String(corsOrigins)
          .split(',')
          .map((s: string) => s.trim())
          .filter((s: string) => s.length > 0);
        return JSON.stringify(arr.length > 0 ? arr : ['https://voj-audiobooks.vercel.app']);
      })();
      fargate = new ecsPatterns.ApplicationLoadBalancedFargateService(this, 'Service', {
        cluster,
        cpu: 512,
        memoryLimitMiB: 1024,
        desiredCount: 2,
        publicLoadBalancer: true,
        taskImageOptions: {
          image: ecs.ContainerImage.fromEcrRepository(repo),
          containerPort: 8000,
          logDriver: ecs.LogDrivers.awsLogs({ logGroup, streamPrefix: 'api' }),
        environment: {
          ENVIRONMENT: 'production',
          AWS_REGION: cdk.Stack.of(this).region,
          ALLOWED_HOSTS: '["*"]',
          S3_BUCKET_NAME: s3BucketName,
          BOOKS_TABLE_NAME: booksTableName,
          AUDIO_CHAPTERS_TABLE_NAME: audioChaptersTableName,
          CORS_ORIGINS: corsOriginsJson,
          RELEASE_ID: Date.now().toString(),
        },
        },
      });
    }

    // Health check path (use /health which returns 200)
    fargate.targetGroup.configureHealthCheck({ path: '/health' });

    // Outputs
    if (enableDomain) {
      new cdk.CfnOutput(this, 'ServiceURL', { value: `https://${domainName}` });
    }
    new cdk.CfnOutput(this, 'ALBDNS', { value: fargate.loadBalancer.loadBalancerDnsName });
  }
}


