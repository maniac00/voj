"use client";

import { useEffect } from "react";

/**
 * 환경변수 디버깅 컴포넌트
 * 브라우저 콘솔에 환경변수 출력
 */
export function EnvChecker() {
  useEffect(() => {
    console.group("🔍 VOJ Environment Check");
    console.log("API_URL:", process.env.NEXT_PUBLIC_API_URL || "NOT SET");
    console.log("API_BASE:", process.env.NEXT_PUBLIC_API_BASE || "NOT SET");
    console.log("Current Origin:", window.location.origin);
    console.log("Current Pathname:", window.location.pathname);
    console.groupEnd();

    // window 객체에 디버깅 함수 추가
    if (typeof window !== "undefined") {
      (window as any).checkEnv = () => {
        console.group("🔍 VOJ Environment Check (Manual)");
        console.log("API_URL:", process.env.NEXT_PUBLIC_API_URL || "NOT SET");
        console.log("API_BASE:", process.env.NEXT_PUBLIC_API_BASE || "NOT SET");
        console.log("Current Origin:", window.location.origin);
        console.groupEnd();

        return {
          apiUrl: process.env.NEXT_PUBLIC_API_URL || "NOT SET",
          apiBase: process.env.NEXT_PUBLIC_API_BASE || "NOT SET",
          origin: window.location.origin,
        };
      };
      console.info(
        "💡 Tip: Run window.checkEnv() to check environment variables",
      );
    }
  }, []);

  return null; // 렌더링하지 않음
}
