/**
 * 환경변수 디버깅 유틸리티
 * 브라우저 콘솔에서 사용 가능
 */

export function logEnvVars() {
  console.group("🔍 Environment Variables");
  console.log("NEXT_PUBLIC_API_URL:", process.env.NEXT_PUBLIC_API_URL);
  console.log("NEXT_PUBLIC_API_BASE:", process.env.NEXT_PUBLIC_API_BASE);
  console.log("NODE_ENV:", process.env.NODE_ENV);
  console.groupEnd();
}

export function getApiConfig() {
  const config = {
    apiUrl: process.env.NEXT_PUBLIC_API_URL,
    apiBase: process.env.NEXT_PUBLIC_API_BASE,
    nodeEnv: process.env.NODE_ENV,
  };

  console.log("📋 API Configuration:", config);
  return config;
}

// 자동 실행 (개발 환경에서만)
if (typeof window !== "undefined" && process.env.NODE_ENV === "development") {
  console.log("🚀 Debug ENV loaded");
  logEnvVars();
}
