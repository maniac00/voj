import { fetchJson } from "@/lib/api";
import { apiBase } from "@/lib/config";

export type UserDto = {
  id: number;
  email: string;
  display_name: string | null;
  photo_url: string | null;
  status: "pending" | "approved" | "suspended";
  role: "user" | "admin";
  can_access_copyrighted: boolean;
  created_at: string;
  updated_at: string;
};

export async function fetchUsers(
  statusFilter?: string,
): Promise<UserDto[]> {
  const params = statusFilter ? `?status=${statusFilter}` : "";
  return fetchJson<UserDto[]>(`${apiBase()}/users${params}`);
}

export async function updateUserStatus(
  userId: number,
  status: "pending" | "approved" | "suspended",
): Promise<UserDto> {
  return fetchJson<UserDto>(`${apiBase()}/users/${userId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function deleteUser(userId: number): Promise<void> {
  await fetchJson<void>(`${apiBase()}/users/${userId}`, {
    method: "DELETE",
  });
}

export async function updateUserCopyrightAccess(
  userId: number,
  canAccess: boolean,
): Promise<UserDto> {
  return fetchJson<UserDto>(`${apiBase()}/users/${userId}/copyright-access`, {
    method: "PATCH",
    body: JSON.stringify({ can_access_copyrighted: canAccess }),
  });
}
