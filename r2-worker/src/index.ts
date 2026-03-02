interface Env {
  RELEASES: R2Bucket;
  AUTH_SECRET: string;
}

/**
 * HMAC-SHA256 토큰 검증
 * message = "{key}:{exp_unix}"
 */
async function validateToken(
  secret: string,
  key: string,
  token: string,
  exp: string,
): Promise<boolean> {
  const expNum = parseInt(exp, 10);
  if (isNaN(expNum) || Math.floor(Date.now() / 1000) > expNum) {
    return false;
  }

  const encoder = new TextEncoder();
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );

  const message = encoder.encode(`${key}:${exp}`);
  const tokenBytes = new Uint8Array(
    token.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16)),
  );

  return crypto.subtle.verify("HMAC", cryptoKey, tokenBytes, message);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    // 한글 등 비ASCII 문자가 URL 인코딩된 경우 디코딩하여 R2 키와 일치시킴
    const key = decodeURIComponent(url.pathname.slice(1));

    if (!key) {
      return new Response("Not Found", { status: 404 });
    }

    // APK 파일은 공개 (인증 불필요)
    const isPublic = key.endsWith(".apk");

    if (!isPublic) {
      // HMAC 토큰 검증
      const token = url.searchParams.get("token");
      const exp = url.searchParams.get("exp");

      if (!token || !exp || !env.AUTH_SECRET) {
        return new Response("Unauthorized", { status: 401 });
      }

      const valid = await validateToken(env.AUTH_SECRET, key, token, exp);
      if (!valid) {
        return new Response("Unauthorized", { status: 401 });
      }
    }

    // Range 요청 지원 (오디오 탐색에 필수)
    const rangeHeader = request.headers.get("range");
    let r2Options: R2GetOptions = {};
    if (rangeHeader) {
      const match = rangeHeader.match(/bytes=(\d*)-(\d*)/);
      if (match) {
        const start = match[1] ? parseInt(match[1], 10) : undefined;
        const end = match[2] ? parseInt(match[2], 10) : undefined;
        if (start !== undefined) {
          r2Options.range = end !== undefined
            ? { offset: start, length: end - start + 1 }
            : { offset: start };
        }
      }
    }

    const object = await env.RELEASES.get(key, r2Options);
    if (!object) {
      return new Response("Not Found", { status: 404 });
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set("etag", object.httpEtag);
    headers.set("Accept-Ranges", "bytes");
    headers.set("Cache-Control", "private, max-age=3600");

    // APK: 다운로드 헤더
    if (key.endsWith(".apk")) {
      headers.set("Content-Type", "application/vnd.android.package-archive");
      headers.set(
        "Content-Disposition",
        `attachment; filename="${key.split("/").pop()}"`,
      );
    }

    // Range 응답
    if (rangeHeader && object.range) {
      const range = object.range as { offset: number; length: number };
      const total = object.size;
      const start = range.offset;
      const end = start + range.length - 1;
      headers.set("Content-Range", `bytes ${start}-${end}/${total}`);
      headers.set("Content-Length", String(range.length));
      return new Response(object.body, { status: 206, headers });
    }

    headers.set("Content-Length", String(object.size));
    return new Response(object.body, { headers });
  },
} satisfies ExportedHandler<Env>;
