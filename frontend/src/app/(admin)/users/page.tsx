"use client";

import React, { useCallback, useEffect, useState } from "react";
import { fetchUsers, updateUserStatus, type UserDto } from "@/lib/users";

type StatusFilter = "" | "pending" | "approved" | "suspended";

const STATUS_LABELS: Record<string, string> = {
  pending: "승인 대기",
  approved: "승인됨",
  suspended: "정지됨",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  suspended: "bg-red-100 text-red-800",
};

export default function UsersPage() {
  const [users, setUsers] = useState<UserDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [updating, setUpdating] = useState<number | null>(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchUsers(statusFilter || undefined);
      setUsers(data);
    } catch (e: any) {
      setError(e.message || "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleStatusChange = async (
    userId: number,
    newStatus: "approved" | "suspended" | "pending",
  ) => {
    setUpdating(userId);
    try {
      const updated = await updateUserStatus(userId, newStatus);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? updated : u)),
      );
    } catch (e: any) {
      alert(`상태 변경 실패: ${e.message}`);
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          사용자 관리
        </h1>
        <button
          onClick={loadUsers}
          className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md"
        >
          새로고침
        </button>
      </div>

      {/* Status Filter */}
      <div className="flex gap-2 mb-6">
        {(["", "pending", "approved", "suspended"] as StatusFilter[]).map(
          (s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-4 py-2 text-sm rounded-md border ${
                statusFilter === s
                  ? "bg-black text-white border-black"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }`}
            >
              {s === "" ? "전체" : STATUS_LABELS[s]}
            </button>
          ),
        )}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-500">
          불러오는 중...
        </div>
      ) : users.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          사용자가 없습니다.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">이메일</th>
                <th className="py-3 px-4">이름</th>
                <th className="py-3 px-4">상태</th>
                <th className="py-3 px-4">역할</th>
                <th className="py-3 px-4">가입일</th>
                <th className="py-3 px-4">작업</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr
                  key={user.id}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-3 px-4 text-sm">{user.id}</td>
                  <td className="py-3 px-4 text-sm">{user.email}</td>
                  <td className="py-3 px-4 text-sm">
                    {user.display_name || "-"}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                        STATUS_COLORS[user.status] || ""
                      }`}
                    >
                      {STATUS_LABELS[user.status] || user.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm">
                    {user.role === "admin" ? "관리자" : "사용자"}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-500">
                    {user.created_at
                      ? new Date(user.created_at).toLocaleDateString("ko-KR")
                      : "-"}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex gap-2">
                      {user.status !== "approved" && (
                        <button
                          onClick={() =>
                            handleStatusChange(user.id, "approved")
                          }
                          disabled={updating === user.id}
                          className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          승인
                        </button>
                      )}
                      {user.status !== "suspended" && (
                        <button
                          onClick={() =>
                            handleStatusChange(user.id, "suspended")
                          }
                          disabled={updating === user.id}
                          className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                        >
                          정지
                        </button>
                      )}
                      {user.status === "suspended" && (
                        <button
                          onClick={() =>
                            handleStatusChange(user.id, "pending")
                          }
                          disabled={updating === user.id}
                          className="px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
                        >
                          대기로
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
