"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getChapters,
  reorderChapter,
  deleteChapter,
  updateChapter,
  type ChapterDto,
  getStreamingUrlApi,
} from "@/lib/audio";
import { ChapterEditDialog } from "@/components/audio/chapter-edit-dialog";
import { getBook, BookDto } from "@/lib/api";
import { FileUploadForm } from "@/components/audio/file-upload-form";
import {
  ChapterList,
  ChapterStats,
  ChapterSearch,
} from "@/components/audio/chapter-list";
// Remove realtime logs/status imports
// import { RealTimeLogs } from '@/components/logs/real-time-logs'
// import { RealTimeStatus } from '@/components/status/real-time-status'
// import { LogManager } from '@/components/logs/log-manager'
import { AudioPlayer } from "@/components/audio/audio-player";
import { ContinuousPlayer } from "@/components/audio/playlist-manager";
import {
  PlaybackStateManager,
  PlaybackStats,
} from "@/components/audio/playback-state-manager";
import { useNotification } from "@/contexts/notification-context";
import { ErrorState, LoadingState } from "@/components/ui/error-state";

export default function BookAudiosPage() {
  const params = useParams();
  const bookId = String(params?.bookId || "");
  const [book, setBook] = useState<BookDto | null>(null);
  const [chapters, setChapters] = useState<ChapterDto[]>([]);
  const [filteredChapters, setFilteredChapters] = useState<ChapterDto[]>([]);
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(
    null,
  );
  // remove logs/state toggles
  // const [showLogs, setShowLogs] = useState(true)
  // const [showLogManager, setShowLogManager] = useState(false)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { success, error: showError } = useNotification();

  // remove currentLogs state
  // const [currentLogs, setCurrentLogs] = useState<any[]>([])

  useEffect(() => {
    const loadData = async () => {
      if (!bookId) return;

      try {
        // 책 정보와 챕터 목록을 병렬로 로드
        const [bookData, chaptersData] = await Promise.all([
          getBook(bookId),
          getChapters(bookId).catch(() => []),
        ]);

        setBook(bookData);
        const sortedChapters = chaptersData.sort(
          (a, b) => a.chapter_number - b.chapter_number,
        );
        setChapters(sortedChapters);
        setFilteredChapters(sortedChapters);

        // 첫 번째 챕터를 기본 선택
        if (sortedChapters.length > 0 && !selectedChapterId) {
          setSelectedChapterId(sortedChapters[0].chapter_id);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "데이터를 불러오는데 실패했습니다.",
        );
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [bookId]);

  const handleUploadComplete = (chapterId: string, fileName: string) => {
    // 챕터 목록 새로고침
    getChapters(bookId)
      .then((data) => {
        const sortedChapters = data.sort(
          (a, b) => a.chapter_number - b.chapter_number,
        );
        setChapters(sortedChapters);
        setFilteredChapters(sortedChapters);
      })
      .catch(() => {
        showError("챕터 목록을 새로고침하는데 실패했습니다.");
      });

    // 책 정보도 새로고침하여 총 챕터 수/통계를 반영
    getBook(bookId)
      .then((data) => setBook(data))
      .catch(() => {});
  };

  const handleChapterReorder = async (
    chapterId: string,
    direction: "up" | "down",
  ) => {
    const chapter = chapters.find((c) => c.chapter_id === chapterId);
    if (!chapter) return;

    try {
      const newNumber =
        direction === "up"
          ? Math.max(1, chapter.chapter_number - 1)
          : chapter.chapter_number + 1;

      await reorderChapter(bookId, chapter.chapter_id, newNumber);

      // 스왑된 상대 챕터도 반영하기 위해 전체 목록 새로고침
      const freshChapters = await getChapters(bookId);
      const sortedChapters = freshChapters.sort(
        (a, b) => a.chapter_number - b.chapter_number,
      );
      setChapters(sortedChapters);
      setFilteredChapters(sortedChapters);
    } catch (err) {
      throw err; // ChapterList에서 에러 처리
    }
  };

  const handleChapterDelete = async (chapterId: string) => {
    try {
      await deleteChapter(bookId, chapterId);
      const updatedChapters = chapters.filter(
        (c) => c.chapter_id !== chapterId,
      );
      setChapters(updatedChapters);
      setFilteredChapters(updatedChapters);
    } catch (err) {
      throw err; // ChapterList에서 에러 처리
    }
  };

  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [showPlaylist, setShowPlaylist] = useState(false);

  const handleChapterPlay = async (chapterId: string) => {
    try {
      // 스트리밍 URL 요청 (절대 경로 API 사용)
      const streamData = await getStreamingUrlApi(bookId, chapterId);

      // 재생 시작
      setCurrentlyPlaying(chapterId);
      setAudioUrl(streamData.streaming_url);

      success("오디오 재생을 시작합니다.");
    } catch (error) {
      showError(
        `재생 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
      );
    }
  };

  const handleAudioStop = () => {
    setCurrentlyPlaying(null);
    setAudioUrl(null);
  };

  // 스트리밍 URL 생성 (플레이리스트용)
  const getStreamingUrl = async (chapterId: string): Promise<string> => {
    const streamData = await getStreamingUrlApi(bookId, chapterId);
    return streamData.streaming_url;
  };

  const [editingChapter, setEditingChapter] = useState<ChapterDto | null>(null);

  const handleChapterEdit = (chapterId: string) => {
    const chapter = chapters.find((c) => c.chapter_id === chapterId);
    if (chapter) {
      setEditingChapter(chapter);
    }
  };

  const handleChapterSave = async (
    chapterId: string,
    data: { title: string },
  ) => {
    const updated = await updateChapter(bookId, chapterId, data);
    const updatedChapters = chapters
      .map((c) => (c.chapter_id === chapterId ? updated : c))
      .sort((a, b) => a.chapter_number - b.chapter_number);
    setChapters(updatedChapters);
    setFilteredChapters(updatedChapters);
    success(`"${updated.title}" 챕터가 수정되었습니다.`);
  };

  if (loading) {
    return <LoadingState message="책 정보와 챕터 목록을 불러오는 중..." />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorState
          title="데이터 로드 실패"
          message={error}
          showRetry={true}
          onRetry={() => window.location.reload()}
          showHome={true}
        />
      </div>
    );
  }

  if (!book) {
    return (
      <div className="p-6">
        <ErrorState
          title="책을 찾을 수 없습니다"
          message="요청하신 책이 존재하지 않거나 접근 권한이 없습니다."
          showHome={true}
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* 헤더 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              오디오 파일 관리
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              <strong>"{book.title}"</strong> - {book.author}
            </p>
          </div>
          <Link
            href={`/books/${bookId}`}
            className="text-gray-600 hover:text-gray-900 text-sm"
          >
            ← 책 편집으로 돌아가기
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* 왼쪽: 파일 업로드 및 챕터 관리 */}
        <div className="xl:col-span-2 space-y-6">
          {/* 파일 업로드 */}
          <FileUploadForm
            bookId={bookId}
            onUploadComplete={handleUploadComplete}
            onUploadStart={(fileName) => {
              console.log(`Upload started: ${fileName}`);
            }}
          />

          {/* 챕터 통계 */}
          {chapters.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <ChapterStats chapters={chapters} />
              <PlaybackStats bookId={bookId} />
            </div>
          )}

          {/* 챕터 검색 및 필터 */}
          {chapters.length > 0 && (
            <ChapterSearch chapters={chapters} onFilter={setFilteredChapters} />
          )}

          {/* 챕터 목록 */}
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900">챕터 목록</h2>
                <div className="text-sm text-gray-600">
                  {filteredChapters.length !== chapters.length
                    ? `${filteredChapters.length}개 표시 (전체 ${chapters.length}개)`
                    : `총 ${chapters.length}개 챕터`}
                </div>
              </div>
            </div>

            <div className="p-6">
              <ChapterList
                chapters={filteredChapters}
                onReorder={handleChapterReorder}
                onDelete={handleChapterDelete}
                onPlay={handleChapterPlay}
                onEdit={handleChapterEdit}
                onSelect={setSelectedChapterId}
                selectedChapterId={selectedChapterId || undefined}
                currentlyPlayingId={currentlyPlaying || undefined}
              />
            </div>
          </div>
        </div>

        {/* 오른쪽: 보조 패널 */}
        <div className="space-y-6">
          {/* 모니터링 컨트롤: 로그/상태 버튼 제거, 플레이리스트만 유지 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">모니터링</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowPlaylist(!showPlaylist)}
                  className={`px-3 py-1 text-sm rounded-md ${
                    showPlaylist
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-700"
                  } hover:opacity-80`}
                >
                  {showPlaylist ? "플레이리스트 숨기기" : "연속 재생"}
                </button>
              </div>
            </div>
          </div>

          {/* 오디오 플레이어 */}
          {currentlyPlaying && audioUrl && (
            <div className="bg-white rounded-lg border border-gray-200">
              <div className="px-4 py-3 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">
                    오디오 플레이어
                  </h3>
                  <button
                    onClick={handleAudioStop}
                    className="text-sm text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
                  >
                    닫기
                  </button>
                </div>
              </div>
              <div className="p-4">
                <AudioPlayer
                  src={audioUrl}
                  title={
                    chapters.find((c) => c.chapter_id === currentlyPlaying)
                      ?.title || "오디오"
                  }
                  onPlay={() => console.log("Audio started playing")}
                  onPause={() => console.log("Audio paused")}
                  onEnded={() => {
                    console.log("Audio ended");
                  }}
                  onError={(error) => {
                    showError(`재생 오류: ${error}`);
                    handleAudioStop();
                  }}
                />
              </div>
            </div>
          )}

          {/* 재생 기록 및 상태 */}
          <PlaybackStateManager
            bookId={bookId}
            chapterId={selectedChapterId || undefined}
            onResumePlayback={async (chapterId, position) => {
              await handleChapterPlay(chapterId);
            }}
          />

          {/* 연속 재생 플레이리스트 */}
          {showPlaylist && (
            <ContinuousPlayer
              chapters={chapters}
              bookId={bookId}
              onGetStreamingUrl={getStreamingUrl}
            />
          )}
        </div>
      </div>

      {/* 챕터 편집 다이얼로그 */}
      <ChapterEditDialog
        isOpen={editingChapter !== null}
        chapter={editingChapter}
        onClose={() => setEditingChapter(null)}
        onSave={handleChapterSave}
      />
    </div>
  );
}
