import { apiBase } from "@/lib/config";
import { fetchJson } from "@/lib/api";

export type ChapterDto = {
  chapter_id: string;
  book_id: string;
  chapter_number: number;
  title: string;
  description?: string | null;
  file_name: string;
  file_size: number;
  duration: number;
  status: string;
  created_at?: string;
  updated_at?: string;
};

export async function getChapters(bookId: string): Promise<ChapterDto[]> {
  return fetchJson<ChapterDto[]>(
    `${apiBase()}/audio/${encodeURIComponent(bookId)}/chapters`,
  );
}

export async function reorderChapter(
  bookId: string,
  chapterId: string,
  newNumber: number,
): Promise<ChapterDto> {
  return fetchJson<ChapterDto>(
    `${apiBase()}/audio/${encodeURIComponent(bookId)}/chapters/${encodeURIComponent(chapterId)}?new_number=${newNumber}`,
    { method: "PUT" },
  );
}

export async function deleteChapter(
  bookId: string,
  chapterId: string,
): Promise<{ message: string }> {
  return fetchJson<{ message: string }>(
    `${apiBase()}/audio/${encodeURIComponent(bookId)}/chapters/${encodeURIComponent(chapterId)}`,
    { method: "DELETE" },
  );
}

export type StreamUrlResponse = {
  streaming_url: string;
  expires_at: string;
  duration: number;
};

export async function getStreamingUrlApi(
  bookId: string,
  chapterId: string,
): Promise<StreamUrlResponse> {
  return fetchJson<StreamUrlResponse>(
    `${apiBase()}/audio/${encodeURIComponent(bookId)}/chapters/${encodeURIComponent(chapterId)}/stream`,
  );
}
