import { FFmpeg } from "@ffmpeg/ffmpeg";
import { fetchFile, toBlobURL } from "@ffmpeg/util";

let ffmpeg: FFmpeg | null = null;

async function getFFmpeg(): Promise<FFmpeg> {
  if (ffmpeg && ffmpeg.loaded) return ffmpeg;
  ffmpeg = new FFmpeg();
  const baseURL = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/esm";
  await ffmpeg.load({
    coreURL: await toBlobURL(`${baseURL}/ffmpeg-core.js`, "text/javascript"),
    wasmURL: await toBlobURL(`${baseURL}/ffmpeg-core.wasm`, "application/wasm"),
  });
  return ffmpeg;
}

export function isWavFile(file: File): boolean {
  const ext = file.name.split(".").pop()?.toLowerCase();
  return ext === "wav";
}

export async function convertWavToM4a(
  file: File,
  onProgress?: (ratio: number) => void,
): Promise<File> {
  const ff = await getFFmpeg();

  const progressHandler = onProgress
    ? ({ progress }: { progress: number }) => onProgress(progress)
    : null;

  if (progressHandler) {
    ff.on("progress", progressHandler);
  }

  const inputName = "input.wav";
  const outputName = "output.m4a";

  await ff.writeFile(inputName, await fetchFile(file));
  await ff.exec([
    "-i", inputName,
    "-c:a", "aac",
    "-b:a", "128k",
    "-ar", "44100",
    "-ac", "1",
    outputName,
  ]);

  const data = await ff.readFile(outputName);
  await ff.deleteFile(inputName);
  await ff.deleteFile(outputName);

  if (progressHandler) {
    ff.off("progress", progressHandler);
  }

  const m4aName = file.name.replace(/\.wav$/i, ".m4a");
  return new File([data as BlobPart], m4aName, { type: "audio/mp4" });
}
