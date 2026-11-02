import type { NextRequest } from "next/server";
import { backendFetch } from "@/lib/backend";

const FORWARDED_RESPONSE_HEADERS = [
  "content-type",
  "content-disposition",
  "cache-control",
  "etag",
  "last-modified",
];

export const maxDuration = 60;

async function handler(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  const target = `/${path.join("/")}${request.nextUrl.search}`;

  const headers = new Headers();
  for (const name of ["content-type", "accept", "accept-language"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const init: RequestInit = { method: request.method, headers };
  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.arrayBuffer();
  }

  const response = await backendFetch(target, init);
  const responseHeaders = new Headers();
  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = response.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }

  if (response.status === 204 || response.status === 304) {
    return new Response(null, {
      status: response.status,
      headers: responseHeaders,
    });
  }

  const body = await response.arrayBuffer();
  responseHeaders.set("content-length", String(body.byteLength));

  return new Response(body, {
    status: response.status,
    headers: responseHeaders,
  });
}

export const GET = handler;
export const HEAD = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
