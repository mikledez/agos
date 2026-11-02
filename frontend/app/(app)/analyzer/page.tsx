import AnalyzerClient from "./analyzer-client";

export default async function AnalyzerPage({
  searchParams,
}: {
  searchParams: Promise<{ session?: string }>;
}) {
  const { session } = await searchParams;
  const parsed = session ? Number(session) : null;
  const sessionId = parsed && Number.isInteger(parsed) ? parsed : null;

  return <AnalyzerClient sessionId={sessionId} />;
}
