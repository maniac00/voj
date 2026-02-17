"use client";

import React, { useState, useRef } from "react";
import { useNotification } from "@/contexts/notification-context";
import { useFileUpload, useBatchFileUpload } from "@/hooks/use-file-upload";
import { BatchUploadProgress } from "@/components/audio/upload-progress";
import {
  validateAudioFiles,
  analyzeAudiobookSeries,
  checkDuplicateFiles,
  quickValidateAudioFile,
} from "@/lib/audio-validation";
import { useUploadErrorHandler } from "@/hooks/use-upload-error-handler";
import {
  NetworkStatusIndicator,
  UploadTroubleshooting,
} from "@/components/audio/upload-error-handler";
import { ErrorAnalyzer } from "@/components/error/error-analyzer";

interface FileUploadFormProps {
  bookId: string;
  onUploadComplete?: (chapterId: string, fileName: string) => void;
  onUploadStart?: (fileName: string) => void;
  className?: string;
}

export function FileUploadForm({
  bookId,
  onUploadComplete,
  onUploadStart,
  className = "",
}: FileUploadFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { success, error: showError, warning } = useNotification();
  const { handleUploadError, resetRetryCount } = useUploadErrorHandler();
  const {
    uploadItems,
    isUploading,
    addFiles,
    uploadAll,
    cancelUpload,
    removeItem,
    retryItem,
    clearCompleted,
  } = useBatchFileUpload();

  // 지원되는 오디오 파일 형식
  // mp4/m4a/mp3 직접 업로드 + WAV (클라이언트에서 M4A로 자동 변환)
  const acceptedFormats = [".mp4", ".m4a", ".mp3", ".wav"];
  const maxFileSize = 500 * 1024 * 1024; // 500MB (WAV 대응)

  const [validationResults, setValidationResults] = useState<Map<string, any>>(
    new Map(),
  );
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [processingPhase, setProcessingPhase] = useState<"validating" | "uploading">("validating");

  const handleFileSelect = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const files = Array.from(event.target.files || []);

    if (files.length === 0) return;

    setShowUploadModal(true);
    setProcessingPhase("validating");

    try {
      // 1. 중복 파일 검사
      const { duplicates, uniqueFiles } = checkDuplicateFiles(files);

      if (duplicates.length > 0) {
        const duplicateNames = duplicates
          .map((d) => d.duplicate.name)
          .join(", ");
        setShowUploadModal(false);
        showError(`중복된 파일이 있습니다: ${duplicateNames}`);
        return;
      }

      // 2. 종합적인 파일 검증
      const validationResult = await validateAudioFiles(uniqueFiles, {
        maxFileSize,
        minDuration: 5, // 5초 이상
        maxDuration: 2 * 60 * 60, // 2시간 이하
        allowedFormats: acceptedFormats,
      });

      // 3. 검증 실패 파일 처리
      if (validationResult.invalidFiles.length > 0) {
        validationResult.invalidFiles.forEach(({ file, result }) => {
          handleUploadError(file.name, file.name, result.errors.join("; "));
        });

        if (validationResult.validFiles.length === 0) {
          setShowUploadModal(false);
          return;
        }
      }

      // 4. 오디오북 시리즈 분석
      const seriesAnalysis = analyzeAudiobookSeries(
        validationResult.validFiles,
      );

      if (seriesAnalysis.warnings.length > 0) {
        seriesAnalysis.warnings.forEach((warningMsg) => {
          warning(warningMsg, "파일 분석 경고");
        });
      }

      // 5. 검증 결과 저장
      const newValidationResults = new Map(validationResults);
      validationResult.validFiles.forEach((file) => {
        const fileValidation = validationResult.invalidFiles.find(
          (f) => f.file === file,
        )?.result;
        if (fileValidation) {
          newValidationResults.set(file.name, fileValidation);
        }
      });
      setValidationResults(newValidationResults);

      // 6. 유효한 파일들을 업로드 목록에 추가
      const newItems = addFiles(validationResult.validFiles, bookId);

      // 7. 업로드 시작 알림
      validationResult.validFiles.forEach((file) => {
        onUploadStart?.(file.name);
      });

      // 8. 총 정보 표시
      if (validationResult.totalDuration) {
        const totalMinutes = Math.round(validationResult.totalDuration / 60);
        const totalSizeMB = (
          validationResult.totalSize /
          (1024 * 1024)
        ).toFixed(1);
        success(
          `${validationResult.validFiles.length}개 파일 선택됨 (총 ${totalMinutes}분, ${totalSizeMB}MB)`,
        );
      }

      // 9. 업로드 시작 (방금 추가한 목록으로 즉시 시작)
      setProcessingPhase("uploading");
      await uploadAll(bookId, newItems);
      setShowUploadModal(false);
    } catch (error) {
      setShowUploadModal(false);
      showError(
        `파일 처리 중 오류가 발생했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
      );
    } finally {
      // 파일 입력 초기화
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // 업로드 완료 콜백
  const handleUploadComplete = (chapterId: string, fileName: string) => {
    onUploadComplete?.(chapterId, fileName);
    success(`"${fileName}" 업로드가 완료되었습니다.`);
  };

  return (
    <div className={className}>
      {/* 네트워크 상태 표시기 */}
      <NetworkStatusIndicator />

      {/* 파일 선택 영역 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          오디오 파일 업로드
        </h2>

        <div className="text-center">
          <div className="mb-4">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <div className="mb-4">
            <label
              htmlFor="audio-file-input"
              className="cursor-pointer inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
            >
              <svg
                className="mr-2 h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              오디오 파일 선택
            </label>
            <input
              ref={fileInputRef}
              id="audio-file-input"
              type="file"
              multiple
              accept={acceptedFormats.join(",")}
              onChange={handleFileSelect}
              className="sr-only"
              disabled={isUploading}
              aria-describedby="file-upload-help"
            />
          </div>

          <div id="file-upload-help" className="text-sm text-gray-600">
            <p>지원 형식: {acceptedFormats.join(", ")}</p>
            <p>최대 파일 크기: {Math.round(maxFileSize / (1024 * 1024))}MB</p>
            <p>여러 파일을 동시에 선택할 수 있습니다.</p>
            <p className="text-amber-600">WAV 파일은 자동으로 M4A로 변환됩니다. MP3는 변환 없이 업로드됩니다.</p>
          </div>
        </div>
      </div>

      {/* 업로드 진행 모달 */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* 배경 오버레이 */}
          <div className="absolute inset-0 bg-black/50" />

          {/* 모달 본체 */}
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {processingPhase === "validating"
                ? "파일 검증 중..."
                : "업로드 처리 중..."}
            </h3>

            <p className="text-sm text-gray-500 mb-4">
              {processingPhase === "validating"
                ? "파일을 분석하고 검증하고 있습니다. 잠시만 기다려 주세요."
                : "업로드가 완료될 때까지 이 창이 유지됩니다. 잠시만 기다려 주세요."}
            </p>

            {/* 업로드 항목이 있으면 진행률 표시 */}
            {uploadItems.length > 0 && (
              <BatchUploadProgress
                items={uploadItems.map((item) => ({
                  id: item.id,
                  file: item.file,
                  progress: item.progress,
                  status: item.status,
                  error: item.error,
                }))}
                onCancel={cancelUpload}
                onRetry={retryItem}
                onRemove={removeItem}
                onClearCompleted={clearCompleted}
              />
            )}

            {/* 검증 중 로딩 스피너 */}
            {processingPhase === "validating" && uploadItems.length === 0 && (
              <div className="flex items-center justify-center py-8">
                <svg
                  className="animate-spin h-8 w-8 text-gray-600"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 문제 해결 가이드 */}
      <UploadTroubleshooting className="mt-6" />
    </div>
  );
}

interface QuickUploadButtonProps {
  onFileSelect: (files: File[]) => void;
  disabled?: boolean;
  className?: string;
}

export function QuickUploadButton({
  onFileSelect,
  disabled = false,
  className = "",
}: QuickUploadButtonProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length > 0) {
      onFileSelect(files);
    }
  };

  return (
    <div className={className}>
      <button
        onClick={handleClick}
        disabled={disabled}
        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg
          className="mr-2 h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v16m8-8H4"
          />
        </svg>
        오디오 추가
      </button>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".mp4,.m4a,.mp3,.wav"
        onChange={handleFileChange}
        className="sr-only"
        disabled={disabled}
      />
    </div>
  );
}
