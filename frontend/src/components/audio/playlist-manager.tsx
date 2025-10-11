"use client";

import React, { useState, useEffect } from "react";
import { ChapterDto } from "@/lib/audio";
import {
  usePlaylist,
  savePlaylistState,
  loadPlaylistState,
} from "@/hooks/use-playlist";
import { AudioPlayer } from "@/components/audio/audio-player";
import { useNotification } from "@/contexts/notification-context";

interface PlaylistManagerProps {
  chapters: ChapterDto[];
  bookId: string;
  onGetStreamingUrl: (chapterId: string) => Promise<string>;
  className?: string;
}

export function PlaylistManager({
  chapters,
  bookId,
  onGetStreamingUrl,
  className = "",
}: PlaylistManagerProps) {
  const { success, error: showError } = useNotification();
  const [streamingUrls, setStreamingUrls] = useState<Map<string, string>>(
    new Map(),
  );
  const [currentStreamingUrl, setCurrentStreamingUrl] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(false);

  const {
    state,
    playOrder,
    setPlaylist,
    getCurrentChapter,
    nextChapter,
    previousChapter,
    goToChapter,
    setPlaying,
    setCurrentTime,
    toggleShuffle,
    cycleRepeat,
    toggleAutoAdvance,
    handleChapterEnd,
    getPlaylistStats,
  } = usePlaylist({
    autoAdvance: true,
    onChapterChange: handleChapterChange,
    onPlaylistEnd: () => {
      success("플레이리스트 재생이 완료되었습니다.");
      setCurrentStreamingUrl(null);
    },
  });

  // 챕터 변경 핸들러
  async function handleChapterChange(chapterId: string) {
    setLoading(true);

    try {
      // 캐시된 URL 확인
      if (streamingUrls.has(chapterId)) {
        setCurrentStreamingUrl(streamingUrls.get(chapterId)!);
      } else {
        // 새 URL 생성
        const url = await onGetStreamingUrl(chapterId);
        setStreamingUrls((prev) => new Map(prev).set(chapterId, url));
        setCurrentStreamingUrl(url);
      }
    } catch (error) {
      showError(
        `스트리밍 URL 생성 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
      );
    } finally {
      setLoading(false);
    }
  }

  // 챕터 목록 업데이트 시 플레이리스트 설정
  useEffect(() => {
    setPlaylist(chapters);
  }, [chapters, setPlaylist]);

  // 플레이리스트 상태 저장
  useEffect(() => {
    if (state.items.length > 0) {
      savePlaylistState(bookId, state);
    }
  }, [bookId, state]);

  // 플레이리스트 상태 복원
  useEffect(() => {
    const savedState = loadPlaylistState(bookId);
    if (savedState && savedState.items) {
      // 저장된 상태와 현재 챕터 목록 비교하여 유효한 것만 복원
      const validItems = savedState.items.filter((savedItem) =>
        chapters.some(
          (chapter) =>
            chapter.chapter_id === savedItem.chapter_id &&
            chapter.status === "ready",
        ),
      );

      if (validItems.length > 0) {
        // 현재 chapters 중에서 유효 아이템 순서로 원복
        const restoreChapters = validItems
          .map((saved) =>
            chapters.find((c) => c.chapter_id === saved.chapter_id),
          )
          .filter(Boolean) as typeof chapters;
        setPlaylist(restoreChapters);
      }
    }
  }, [bookId, chapters]);

  const currentChapter = getCurrentChapter();
  const stats = getPlaylistStats();

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, "0")}`;
    }
  };

  const getRepeatIcon = () => {
    switch (state.repeat) {
      case "none":
        return "🔁";
      case "one":
        return "🔂";
      case "all":
        return "🔁";
      default:
        return "🔁";
    }
  };

  const getRepeatText = () => {
    switch (state.repeat) {
      case "none":
        return "반복 없음";
      case "one":
        return "한 곡 반복";
      case "all":
        return "전체 반복";
      default:
        return "반복 없음";
    }
  };

  if (state.items.length === 0) {
    return (
      <div
        className={`bg-gray-50 border border-gray-200 rounded-lg p-6 text-center ${className}`}
      >
        <svg
          className="mx-auto h-12 w-12 text-gray-400 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          플레이리스트가 비어있습니다
        </h3>
        <p className="text-gray-600">재생 가능한 챕터가 없습니다.</p>
        <p className="text-sm text-gray-500 mt-2">
          오디오 파일을 업로드하고 처리가 완료되면 플레이리스트에 표시됩니다.
        </p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* 헤더 */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">플레이리스트</h3>
            <p className="text-sm text-gray-600">
              {stats.currentChapterIndex} / {stats.totalChapters} • 총{" "}
              {formatDuration(stats.totalDuration)}
            </p>
          </div>

          {/* 플레이리스트 컨트롤 */}
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleShuffle}
              className={`p-2 rounded ${
                state.shuffle
                  ? "bg-blue-100 text-blue-700"
                  : "bg-gray-100 text-gray-700"
              } hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-blue-500`}
              aria-label={`셔플 ${state.shuffle ? "비활성화" : "활성화"}`}
              title={`셔플 ${state.shuffle ? "ON" : "OFF"}`}
            >
              🔀
            </button>

            <button
              onClick={() => {
                const newMode = cycleRepeat();
                success(`반복 모드: ${getRepeatText()}`);
              }}
              className="p-2 bg-gray-100 text-gray-700 rounded hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label={`반복 모드: ${getRepeatText()}`}
              title={getRepeatText()}
            >
              {getRepeatIcon()}
            </button>

            <button
              onClick={() => {
                toggleAutoAdvance();
                success(
                  `자동 진행 ${state.autoAdvance ? "비활성화" : "활성화"}`,
                );
              }}
              className={`p-2 rounded ${
                state.autoAdvance
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-700"
              } hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-green-500`}
              aria-label={`자동 진행 ${state.autoAdvance ? "비활성화" : "활성화"}`}
              title={`자동 진행 ${state.autoAdvance ? "ON" : "OFF"}`}
            >
              ⏭️
            </button>
          </div>
        </div>
      </div>

      {/* 현재 재생 중인 챕터 */}
      {currentChapter && (
        <div className="px-6 py-4 border-b border-gray-200 bg-blue-50">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-blue-900 truncate">
                현재 재생: {currentChapter.title}
              </h4>
              <p className="text-xs text-blue-700">
                챕터 {currentChapter.chapter_number} •{" "}
                {formatDuration(currentChapter.duration)}
              </p>
            </div>

            {loading && (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            )}
          </div>
        </div>
      )}

      {/* 오디오 플레이어 */}
      {currentStreamingUrl && currentChapter && (
        <div className="p-6 border-b border-gray-200">
          <AudioPlayer
            src={currentStreamingUrl}
            title={currentChapter.title}
            duration={currentChapter.duration}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onEnded={handleChapterEnd}
            onTimeUpdate={setCurrentTime}
            onError={(error) => {
              showError(`재생 오류: ${error}`);
              setPlaying(false);
            }}
          />
        </div>
      )}

      {/* 플레이리스트 목록 */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-md font-medium text-gray-900">챕터 목록</h4>
          <div className="flex items-center space-x-2">
            <button
              onClick={previousChapter}
              disabled={state.currentIndex === 0 && state.repeat !== "all"}
              className="p-2 text-gray-600 hover:text-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
              aria-label="이전 챕터"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>

            <button
              onClick={nextChapter}
              disabled={
                state.currentIndex === state.items.length - 1 &&
                state.repeat !== "all"
              }
              className="p-2 text-gray-600 hover:text-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
              aria-label="다음 챕터"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>
        </div>

        <div className="space-y-2 max-h-64 overflow-y-auto">
          {state.items.map((item, index) => {
            const isCurrentChapter =
              currentChapter?.chapter_id === item.chapter_id;
            const playOrderIndex = state.shuffle
              ? playOrder.findIndex((orderIndex) => orderIndex === index)
              : index;

            return (
              <div
                key={item.chapter_id}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  isCurrentChapter
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:bg-gray-50"
                }`}
                onClick={() => goToChapter(item.chapter_id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    goToChapter(item.chapter_id);
                  }
                }}
                aria-label={`챕터 ${item.chapter_number}: ${item.title}, ${formatDuration(item.duration)}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span
                      className={`flex items-center justify-center w-6 h-6 text-xs font-medium rounded-full ${
                        isCurrentChapter
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {state.shuffle ? playOrderIndex + 1 : item.chapter_number}
                    </span>

                    <div className="flex-1 min-w-0">
                      <h5 className="text-sm font-medium text-gray-900 truncate">
                        {item.title}
                      </h5>
                      <p className="text-xs text-gray-500">
                        {formatDuration(item.duration)}
                      </p>
                    </div>
                  </div>

                  {isCurrentChapter && state.isPlaying && (
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-0.5">
                        <div className="w-1 h-4 bg-blue-600 animate-pulse"></div>
                        <div
                          className="w-1 h-4 bg-blue-600 animate-pulse"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-1 h-4 bg-blue-600 animate-pulse"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                      <span className="text-xs text-blue-600 font-medium">
                        재생 중
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* 플레이리스트 통계 */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
            <div>
              <span className="font-medium">재생 진행률</span>
              <div className="mt-1">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${stats.totalProgress * 100}%` }}
                  />
                </div>
                <div className="flex justify-between mt-1 text-xs">
                  <span>{formatDuration(stats.playedDuration)}</span>
                  <span>{formatDuration(stats.totalDuration)}</span>
                </div>
              </div>
            </div>

            <div>
              <span className="font-medium">남은 시간</span>
              <div className="mt-1 text-lg font-medium text-gray-900">
                {formatDuration(stats.remainingDuration)}
              </div>
              <div className="text-xs text-gray-500">
                약 {Math.ceil(stats.remainingDuration / 60)}분 남음
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface ContinuousPlayerProps {
  chapters: ChapterDto[];
  bookId: string;
  autoStart?: boolean;
  onGetStreamingUrl: (chapterId: string) => Promise<string>;
  className?: string;
}

export function ContinuousPlayer({
  chapters,
  bookId,
  autoStart = false,
  onGetStreamingUrl,
  className = "",
}: ContinuousPlayerProps) {
  const [isActive, setIsActive] = useState(autoStart);
  const { success } = useNotification();

  const readyChapters = chapters.filter((c) => c.status === "ready");

  const handleStartContinuousPlay = () => {
    if (readyChapters.length === 0) {
      return;
    }

    setIsActive(true);
    success(`연속 재생 시작: ${readyChapters.length}개 챕터`);
  };

  const handleStopContinuousPlay = () => {
    setIsActive(false);
    success("연속 재생 중지");
  };

  if (!isActive) {
    return (
      <div
        className={`bg-white rounded-lg border border-gray-200 p-6 text-center ${className}`}
      >
        <svg
          className="mx-auto h-8 w-8 text-gray-400 mb-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m2-10v.01M3 3h18M3 21h18"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">연속 재생</h3>
        <p className="text-gray-600 mb-4">
          모든 챕터를 순서대로 연속 재생합니다.
        </p>
        <button
          onClick={handleStartContinuousPlay}
          disabled={readyChapters.length === 0}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {readyChapters.length === 0
            ? "재생 가능한 챕터 없음"
            : `${readyChapters.length}개 챕터 연속 재생`}
        </button>
      </div>
    );
  }

  return (
    <div className={className}>
      <PlaylistManager
        chapters={chapters}
        bookId={bookId}
        onGetStreamingUrl={onGetStreamingUrl}
      />

      <div className="mt-4 text-center">
        <button
          onClick={handleStopContinuousPlay}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          연속 재생 중지
        </button>
      </div>
    </div>
  );
}
