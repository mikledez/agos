import { redirect } from "next/navigation";

function parseId(value: string | undefined): number | null {
  if (!value) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export default async function AnalyzerPage({
  searchParams,
}: {
  searchParams: Promise<{ session?: string }>;
}) {
  const { session } = await searchParams;
  const folderId = parseId(session);
  redirect(folderId ? `/library?folder=${folderId}` : "/library");
}
