import { redirect } from "next/navigation";
import { LibraryView } from "@/components/library/library-view";
import { backendFetch } from "@/lib/backend";
import { isSearching, parseLibrarySearch, searchQueryString } from "@/lib/search";
import type {
  AthleteProgress,
  ChatMessage,
  Folder,
  ImageDetail,
  SearchResults,
  SprintImage,
} from "@/lib/types";

function parseId(value: string | undefined): number | null {
  if (!value) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

async function fetchJson<T>(
  path: string,
  fallback: T,
  { optional = false }: { optional?: boolean } = {},
): Promise<T> {
  let response: Response;
  try {
    response = await backendFetch(path);
  } catch {
    return fallback;
  }
  if (response.status === 401) redirect("/login");
  if (response.status === 404) return fallback;
  if (!response.ok) {
    const message = `Backend request failed (${response.status}): ${path}`;
    if (!optional) throw new Error(message);
    console.error(message);
    return fallback;
  }
  return (await response.json()) as T;
}

async function buildTrail(folder: Folder): Promise<Folder[]> {
  const trail: Folder[] = [folder];
  const seen = new Set<number>([folder.id]);
  let current = folder;

  while (current.parent_id && !seen.has(current.parent_id)) {
    const parent = await fetchJson<Folder | null>(
      `/sessions/${current.parent_id}`,
      null,
    );
    if (!parent) break;
    trail.unshift(parent);
    seen.add(parent.id);
    current = parent;
  }

  return trail;
}

export default async function LibraryPage({
  searchParams,
}: {
  searchParams: Promise<{
    folder?: string;
    image?: string;
    upload?: string;
    q?: string;
    phase?: string;
    direction?: string;
  }>;
}) {
  const params = await searchParams;
  const folderId = parseId(params.folder);
  const imageId = parseId(params.image);
  const search = parseLibrarySearch(params);
  const searching = isSearching(search);

  // Search covers the whole library, so it ignores the folder.
  const folder = folderId && !searching
    ? await fetchJson<Folder | null>(`/sessions/${folderId}`, null)
    : null;
  if (folderId && !searching && !folder) redirect("/library");

  const [breadcrumb, folders, images, imageDetail, messages, progress, results] = await Promise.all([
    folder ? buildTrail(folder) : Promise.resolve([]),
    searching
      ? Promise.resolve([])
      : fetchJson<Folder[]>(
          folder ? `/sessions?parent_id=${folder.id}` : "/sessions?root=true",
          [],
        ),
    searching
      ? Promise.resolve([])
      : fetchJson<SprintImage[]>(
          folder ? `/images?session_id=${folder.id}` : "/images?root=true",
          [],
        ),
    imageId
      ? fetchJson<ImageDetail | null>(`/images/${imageId}`, null)
      : Promise.resolve(null),
    imageId
      ? fetchJson<ChatMessage[]>(`/images/${imageId}/messages`, [], {
          optional: true,
        })
      : Promise.resolve([]),
    folder?.kind === "athlete"
      ? fetchJson<AthleteProgress | null>(`/sessions/${folder.id}/progress`, null, {
          optional: true,
        })
      : Promise.resolve(null),
    searching
      ? fetchJson<SearchResults>(`/search?${searchQueryString(search)}`, {
          folders: [],
          images: [],
        })
      : Promise.resolve(null),
  ]);

  return (
    <LibraryView
      folder={folder}
      breadcrumb={breadcrumb}
      folders={folders}
      images={images}
      imageDetail={imageDetail}
      messages={messages}
      progress={progress}
      search={search}
      results={results}
      autoOpenUpload={params.upload === "1"}
    />
  );
}
