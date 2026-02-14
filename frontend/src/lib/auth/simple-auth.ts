/**
 * 간단한 세션 기반 인증 유틸리티
 * PRD v2.0 요구사항에 따른 하드코딩 인증 (admin/admin123)
 */

import { apiBase } from "@/lib/config";

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  username: string;
}

export interface User {
  sub: string;
  username: string;
  scope: string;
}

// 토큰 저장 키
const TOKEN_KEY = "voj_access_token";
const USER_KEY = "voj_user_info";

/**
 * 로그인 API 호출
 */
export async function login(
  credentials: LoginCredentials,
): Promise<LoginResponse> {
  const response = await fetch(`${apiBase()}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Login failed" }));
    throw new Error(error.detail || "Login failed");
  }

  return response.json();
}

/**
 * 로그아웃 API 호출
 */
export async function logout(): Promise<void> {
  const token = getStoredToken();

  if (token) {
    try {
      await fetch(`${apiBase()}/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.warn("Logout API call failed:", error);
    }
  }

  // 로컬 스토리지 정리
  clearAuthData();
}

/**
 * 현재 사용자 정보 조회
 */
export async function getCurrentUser(): Promise<User> {
  const token = getStoredToken();

  if (!token) {
    throw new Error("No access token");
  }

  const response = await fetch(`${apiBase()}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    clearAuthData();
    throw new Error("Failed to get user info");
  }

  return response.json();
}

/**
 * 토큰 저장 (쿠키만 사용 - localStorage에 토큰 저장하지 않음)
 */
export function storeToken(token: string): void {
  if (typeof window !== "undefined") {
    // Secure 플래그 추가 (HTTPS에서만 전송), SameSite=Strict
    const secure = window.location.protocol === "https:" ? "; Secure" : "";
    document.cookie = `voj_access_token=${token}; path=/; max-age=86400; SameSite=Strict${secure}`;
  }
}

/**
 * 저장된 토큰 조회 (쿠키에서 파싱)
 */
export function getStoredToken(): string | null {
  if (typeof window !== "undefined") {
    const match = document.cookie
      .split("; ")
      .find((row) => row.startsWith("voj_access_token="));
    return match ? match.split("=")[1] : null;
  }
  return null;
}

/**
 * 사용자 정보 저장
 */
export function storeUser(user: User): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * 저장된 사용자 정보 조회
 */
export function getStoredUser(): User | null {
  if (typeof window !== "undefined") {
    const userStr = localStorage.getItem(USER_KEY);
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
  }
  return null;
}

/**
 * 인증 데이터 정리 (localStorage + 쿠키)
 */
export function clearAuthData(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(USER_KEY);

    // 쿠키 삭제
    document.cookie =
      "voj_access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  }
}

/**
 * 로그인 상태 확인
 */
export function isLoggedIn(): boolean {
  return getStoredToken() !== null;
}

/**
 * API 요청에 인증 헤더 추가
 */
export function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken();

  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }

  return {};
}
