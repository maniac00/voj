"use client";

import React, { useState, useEffect } from "react";
import { ChapterDto } from "@/lib/audio";

interface ChapterEditDialogProps {
  isOpen: boolean;
  chapter: ChapterDto | null;
  onClose: () => void;
  onSave: (chapterId: string, data: { title: string }) => Promise<void>;
}

export function ChapterEditDialog({
  isOpen,
  chapter,
  onClose,
  onSave,
}: ChapterEditDialogProps) {
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen && chapter) {
      setTitle(chapter.title);
      setError("");
      setSaving(false);
    }
  }, [isOpen, chapter]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !saving) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, saving, onClose]);

  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !saving) {
      onClose();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chapter) return;

    const trimmed = title.trim();
    if (!trimmed) {
      setError("챕터 제목을 입력해주세요.");
      return;
    }
    if (trimmed.length > 200) {
      setError("챕터 제목은 200자 이내로 입력해주세요.");
      return;
    }

    setSaving(true);
    setError("");

    try {
      await onSave(chapter.chapter_id, { title: trimmed });
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "저장에 실패했습니다.",
      );
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen || !chapter) return null;

  return (
    <div
      className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4"
      onClick={handleBackgroundClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-dialog-title"
    >
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
        <form onSubmit={handleSubmit}>
          <div className="p-6">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4">
              <svg
                className="h-6 w-6 text-blue-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </div>

            <h3
              id="edit-dialog-title"
              className="text-lg font-medium text-gray-900 text-center mb-4"
            >
              챕터 편집
            </h3>

            <div className="text-xs text-gray-500 text-center mb-4">
              챕터 {chapter.chapter_number} &middot; {chapter.file_name}
            </div>

            <div className="mb-4">
              <label
                htmlFor="chapter-title"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                챕터 제목
              </label>
              <input
                id="chapter-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                placeholder="챕터 제목을 입력하세요"
                maxLength={200}
                disabled={saving}
                autoFocus
              />
              <div className="mt-1 text-xs text-gray-400 text-right">
                {title.length}/200
              </div>
            </div>

            {error && (
              <div className="mb-4 text-sm text-red-600 text-center">
                {error}
              </div>
            )}

            <div className="flex justify-center space-x-3">
              <button
                type="button"
                onClick={onClose}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={saving || !title.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-black border border-transparent rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>저장 중...</span>
                  </div>
                ) : (
                  "저장"
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
