import { auth } from "@/auth";
import { mintBackendToken } from "./backend-token";

export const BACKEND_URL =
  process.env.AGOS_API_URL ?? "http://127.0.0.1:8000";

export async function backendFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const session = await auth();
  if (!session?.user?.email) {
    return Response.json({ detail: "Authentication required" }, { status: 401 });
  }

  const headers = new Headers(init.headers);
  headers.set("authorization", `Bearer ${await mintBackendToken(session.user)}`);

  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export async function backendJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await backendFetch(path, init);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Backend request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function backendAssetUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return `/api/backend${path.startsWith("/") ? path : `/${path}`}`;
}
