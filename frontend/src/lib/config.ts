/**
 * 프론트엔드 전역 API 베이스 URL 중앙화
 */
export function apiBase(): string {
  // 브라우저 환경에서는 항상 상대 경로 사용 (Rewrite 활용)
  if (typeof window !== "undefined") {
    return "/api/v1";
  }
  // 서버 환경에서는 절대 경로 필요
  return (
    process.env.NEXT_PUBLIC_API_BASE ||
    `${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1`
  );
}
