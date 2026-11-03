import { redirect } from "next/navigation";
import { backendFetch } from "@/lib/backend";
import type { ImageDetail } from "@/lib/types";

export default async function ImageRedirectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const parsed = Number(id);
  if (!Number.isInteger(parsed) || parsed <= 0) redirect("/library");

  let response: Response | null = null;
  try {
    response = await backendFetch(`/images/${parsed}`);
  } catch {
    response = null;
  }
  if (response?.status === 401) redirect("/login");

  const detail =
    response?.ok ? ((await response.json()) as ImageDetail) : null;

  const folderId = detail?.image.session_id;
  redirect(
    `/library${folderId ? `?folder=${folderId}&` : "?"}image=${parsed}`,
  );
}
