import { SSTConfig } from "sst";
import { NextjsSite, StackContext } from "sst/constructs";

export default {
  config() {
    return {
      name: "voj-frontend",
      region: "ap-northeast-2",
    };
  },
  stacks(app) {
    app.stack(function Web({ stack }: StackContext) {
      const site = new NextjsSite(stack, "Admin", {
        path: "frontend",
        environment: {
          NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://3u6p7gqsbrwipyxlrwcbzzi2re0ieian.lambda-url.ap-northeast-2.on.aws",
          NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || "https://3u6p7gqsbrwipyxlrwcbzzi2re0ieian.lambda-url.ap-northeast-2.on.aws/api/v1",
        },
        buildCommand: "NODE_ENV=production npm run build",
        cdk: {
          server: {
            memorySize: "1024 MB",
            timeout: "30 seconds",
          },
        },
      });

      stack.addOutputs({
        AdminUrl: site.url || "",
      });
    });
  },
} satisfies SSTConfig;


