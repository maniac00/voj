#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { VojBackendStack } from '../lib/voj-backend-stack';

const app = new cdk.App();

new VojBackendStack(app, 'VojBackendStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-2',
  },
});


