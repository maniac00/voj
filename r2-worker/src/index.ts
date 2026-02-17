interface Env {
  RELEASES: R2Bucket;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const key = url.pathname.slice(1); // 앞의 "/" 제거

    if (!key) {
      return new Response("Not Found", { status: 404 });
    }

    const object = await env.RELEASES.get(key);
    if (!object) {
      return new Response("Not Found", { status: 404 });
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set("etag", object.httpEtag);

    // APK 파일이면 다운로드 헤더 추가
    if (key.endsWith(".apk")) {
      headers.set("Content-Type", "application/vnd.android.package-archive");
      headers.set("Content-Disposition", `attachment; filename="${key.split("/").pop()}"`);
    }

    return new Response(object.body, { headers });
  },
} satisfies ExportedHandler<Env>;
