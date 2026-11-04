import { redirect } from "next/navigation";
import { auth } from "@/auth";
import { AppShell } from "@/components/app-shell";
import { Dashboard } from "@/components/home/dashboard";
import { Landing } from "@/components/home/landing";
import { backendFetch } from "@/lib/backend";
import type { Folder, SprintImage } from "@/lib/types";

async function getJson<T>(path: string, fallback: T): Promise<T> {
  let response: Response;
  try {
    response = await backendFetch(path);
  } catch {
    return fallback;
  }
  if (response.status === 401) redirect("/login");
  if (!response.ok) return fallback;
  return (await response.json()) as T;
}

export default async function HomePage() {
  const session = await auth();

  if (!session?.user?.email) {
    return (
      <AppShell>
        <Landing />
      </AppShell>
    );
  }

  const [folders, images] = await Promise.all([
    getJson<Folder[]>("/sessions?limit=500", []),
    getJson<SprintImage[]>("/images?limit=200", []),
  ]);

  const recentFolders = [...folders].sort(
    (a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  );

  const activityDates = [
    ...folders.map((folder) => folder.updated_at),
    ...images.map((image) => image.updated_at),
  ].sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

  const firstName =
    session.user.name?.trim().split(/\s+/)[0] ||
    session.user.email.split("@")[0] ||
    "athlete";

  return (
    <AppShell>
      <Dashboard
        firstName={firstName}
        folders={recentFolders}
        images={images}
        folderCount={folders.length}
        imageCount={images.length}
        latestActivity={activityDates[0] ?? null}
      />
    </AppShell>
  );
}
