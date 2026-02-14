export const metadata = {
  title: "VOJ Admin",
  description: "Audiobook Admin for Accessibility",
};

import "../app/globals.css";
import React from "react";
import { AuthProvider } from "@/contexts/auth-context";
import { NotificationProvider } from "@/contexts/notification-context";
import { ErrorBoundary } from "@/components/error-boundary";

// 디버그 컴포넌트는 개발 환경에서만 로드
const EnvChecker =
  process.env.NODE_ENV !== "production"
    ? require("@/components/debug/env-checker").EnvChecker
    : () => null;
const RequestInspector =
  process.env.NODE_ENV !== "production"
    ? require("@/components/debug/request-inspector").RequestInspector
    : () => null;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="min-h-screen bg-white text-slate-900 antialiased">
        <EnvChecker />
        <RequestInspector />
        <div className="skip-links">
          <a href="#main" className="skip-link">
            본문으로 건너뛰기
          </a>
          <a href="#navigation" className="skip-link">
            내비게이션으로 건너뛰기
          </a>
          <a href="#search" className="skip-link">
            검색으로 건너뛰기
          </a>
        </div>
        <ErrorBoundary>
          <AuthProvider>
            <NotificationProvider>{children}</NotificationProvider>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
