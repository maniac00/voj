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
    const domainName = this.node.tryGetContext('domainName') || 'api.voj-audiobook.com';
    const hostedZoneName = this.node.tryGetContext('hostedZoneName') || 'voj-audiobook.com';
    const hostedZoneId = this.node.tryGetContext('hostedZoneId');
    const ecrRepoName = this.node.tryGetContext('ecrRepo') || 'voj-backend';

    // VPC (2 AZ)
    const vpc = new ec2.Vpc(this, 'Vpc', {
      maxAzs: 2,
      natGateways: 1,
    });

    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'Cluster', { vpc });

    // ECR Repo (from name)
    const repo = ecr.Repository.fromRepositoryName(this, 'Repo', ecrRepoName);

    // Log group
    const logGroup = new logs.LogGroup(this, 'Logs', {
      logGroupName: '/ecs/voj-backend',
      retention: logs.RetentionDays.ONE_MONTH,
    });

    // Certificate (DNS validated)
    const zone = hostedZoneId
      ? route53.HostedZone.fromHostedZoneAttributes(this, 'Zone', {
          hostedZoneId,
          zoneName: hostedZoneName,
        })
      : route53.HostedZone.fromLookup(this, 'ZoneLookup', {
          domainName: hostedZoneName,
        });

    const cert = new certificatemanager.DnsValidatedCertificate(this, 'Cert', {
      domainName,
      hostedZone: zone,
      region: cdk.Stack.of(this).region,
    });

    // Fargate with ALB (HTTPS)
    const fargate = new ecsPatterns.ApplicationLoadBalancedFargateService(this, 'Service', {
      cluster,
      cpu: 512,
      memoryLimitMiB: 1024,
      desiredCount: 2,
      publicLoadBalancer: true,
      certificate: cert,
      domainName: domainName,
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
        },
      },
    });

    // Health check path
    fargate.targetGroup.configureHealthCheck({ path: '/api/v1/health' });

    // Outputs
    new cdk.CfnOutput(this, 'ServiceURL', { value: `https://${domainName}` });
    new cdk.CfnOutput(this, 'ALBDNS', { value: fargate.loadBalancer.loadBalancerDnsName });
  }
}


