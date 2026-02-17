"use client";

import React, { useEffect, useState } from "react";
import {
  getAnalyticsOverview,
  getAnalyticsUserStats,
  type AnalyticsOverview,
  type UserStat,
} from "@/lib/api";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}시간 ${m}분`;
  return `${m}분`;
}

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div
      className="rounded-lg border border-gray-200 bg-white p-6"
      role="group"
      aria-label={label}
    >
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-gray-900">{value}</p>
      {sub && <p className="mt-1 text-sm text-gray-400">{sub}</p>}
    </div>
  );
}

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [userStats, setUserStats] = useState<UserStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [ov, us] = await Promise.all([
          getAnalyticsOverview(),
          getAnalyticsUserStats(),
        ]);
        setOverview(ov);
        setUserStats(us.users);
      } catch (e: any) {
        setError(e.message || "통계 데이터를 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div
          className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900"
          role="status"
          aria-label="로딩 중"
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-600">
        {error}
      </div>
    );
  }

  if (!overview) return null;

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900">통계</h1>

      {/* 요약 카드 */}
      <section aria-label="요약 통계">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="총 설치 수"
            value={overview.installations.total}
            sub={`활성 ${overview.installations.active}대`}
          />
          <StatCard
            label="일간 활성 사용자"
            value={overview.active_users.daily}
            sub={`주간 ${overview.active_users.weekly} / 월간 ${overview.active_users.monthly}`}
          />
          <StatCard
            label="총 재생 시간"
            value={formatDuration(overview.playback.total_seconds)}
            sub={`${overview.playback.total_sessions}개 세션`}
          />
          <StatCard
            label="평균 세션 길이"
            value={formatDuration(overview.playback.avg_session_seconds)}
            sub={`완료 ${overview.playback.completed_sessions}회`}
          />
        </div>
      </section>

      {/* 차트 영역 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 일별 활성 사용자 */}
        <section
          className="rounded-lg border border-gray-200 bg-white p-6"
          aria-label="일별 활성 사용자 차트"
        >
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            일별 활성 사용자 (최근 7일)
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={overview.daily_active_users}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={12} />
              <YAxis allowDecimals={false} fontSize={12} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="users"
                name="사용자 수"
                stroke="#111827"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </section>

        {/* 인기 도서 */}
        <section
          className="rounded-lg border border-gray-200 bg-white p-6"
          aria-label="인기 도서 차트"
        >
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            인기 도서 (재생 시간 기준)
          </h2>
          {overview.popular_books.length === 0 ? (
            <p className="py-10 text-center text-gray-400">
              아직 재생 데이터가 없습니다.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart
                data={overview.popular_books.map((b) => ({
                  ...b,
                  minutes: Math.round(b.total_seconds / 60),
                }))}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" fontSize={12} />
                <YAxis
                  type="category"
                  dataKey="title"
                  width={120}
                  fontSize={12}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  formatter={(value: number) => [`${value}분`, "재생 시간"]}
                />
                <Bar dataKey="minutes" name="재생 시간(분)" fill="#374151" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>

      {/* 사용자별 통계 테이블 */}
      <section aria-label="사용자별 통계">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          사용자별 통계
        </h2>
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500"
                >
                  사용자
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500"
                >
                  상태
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-right text-xs font-medium uppercase text-gray-500"
                >
                  총 재생 시간
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-right text-xs font-medium uppercase text-gray-500"
                >
                  세션 수
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-right text-xs font-medium uppercase text-gray-500"
                >
                  완독 책
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500"
                >
                  마지막 활동
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500"
                >
                  기기
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {userStats.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-6 py-8 text-center text-gray-400"
                  >
                    사용자 데이터가 없습니다.
                  </td>
                </tr>
              ) : (
                userStats.map((u) => (
                  <tr key={u.user_id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {u.display_name}
                      </div>
                      <div className="text-xs text-gray-400">{u.email}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${
                          u.status === "approved"
                            ? "bg-green-100 text-green-800"
                            : u.status === "pending"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                        }`}
                      >
                        {u.status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-700">
                      {formatDuration(u.total_play_seconds)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-700">
                      {u.session_count}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm text-gray-700">
                      {u.completed_books}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {u.last_activity
                        ? new Date(u.last_activity).toLocaleDateString("ko-KR")
                        : "-"}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {u.app_version || "-"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
