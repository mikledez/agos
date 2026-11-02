/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { redirect } from "next/navigation";
import { backendAssetUrl, backendFetch } from "@/lib/backend";
import { createSession, deleteSession } from "./actions";

type Session = {
  id: number;
  name: string;
  parent_id: number | null;
  created_at: string;
};

type Image = {
  id: number;
  original_filename: string;
  phase: string;
  direction: string;
  created_at: string;
  original_url: string;
  annotated_url: string | null;
};

const PHASE_LABEL: Record<string, string> = {
  toe_off: "Toe off",
  mid_stance: "Mid stance",
  touchdown: "Touchdown",
};

async function getJson<T>(path: string): Promise<T> {
  const response = await backendFetch(path);
  if (response.status === 401) redirect("/login");
  if (!response.ok) {
    throw new Error(`Backend request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export default async function SessionsPage({
  searchParams,
}: {
  searchParams: Promise<{ session?: string }>;
}) {
  const { session: rawSession } = await searchParams;
  const parsed = rawSession ? Number(rawSession) : null;
  const sessionId = parsed && Number.isInteger(parsed) ? parsed : null;

  const [sessions, images, current] = await Promise.all([
    getJson<Session[]>(
      sessionId ? `/sessions?parent_id=${sessionId}` : "/sessions?root=true",
    ),
    getJson<Image[]>(
      sessionId ? `/images?session_id=${sessionId}` : "/images?root=true",
    ),
    sessionId ? getJson<Session>(`/sessions/${sessionId}`) : Promise.resolve(null),
  ]);

  return (
    <main className="main">
      <h1>{current ? current.name : "Library"}</h1>
      <p className="library-nav">
        {current ? (
          <>
            <Link href="/sessions">Library</Link> /{" "}
            <Link
              href={
                current.parent_id
                  ? `/sessions?session=${current.parent_id}`
                  : "/sessions"
              }
            >
              Up
            </Link>{" "}
            /{" "}
          </>
        ) : null}
        <Link href={sessionId ? `/analyzer?session=${sessionId}` : "/analyzer"}>
          Upload an image
        </Link>
      </p>

      <form action={createSession} className="inline-form">
        {sessionId !== null && (
          <input type="hidden" name="parent_id" value={sessionId} />
        )}
        <input
          name="name"
          placeholder={current ? "New sub-session" : "New session"}
          required
        />
        <button type="submit" className="btn">
          Create
        </button>
      </form>

      {current && (
        <form action={deleteSession} className="inline-form">
          <input type="hidden" name="session_id" value={current.id} />
          <input
            type="hidden"
            name="parent_id"
            value={current.parent_id ?? ""}
          />
          <button type="submit" className="btn danger">
            Delete session
          </button>
        </form>
      )}

      <h2>Sessions</h2>
      {sessions.length === 0 ? (
        <p>No sessions yet.</p>
      ) : (
        <ul className="session-list">
          {sessions.map((session) => (
            <li key={session.id}>
              <Link href={`/sessions?session=${session.id}`}>
                {session.name}
              </Link>
            </li>
          ))}
        </ul>
      )}

      <h2>Images</h2>
      {images.length === 0 ? (
        <p>No images here yet.</p>
      ) : (
        <div className="gallery">
          {images.map((image) => {
            const src =
              backendAssetUrl(image.annotated_url ?? image.original_url) ?? "";
            return (
              <Link key={image.id} href={`/images/${image.id}`} className="card">
                <img src={src} alt={image.original_filename} />
                <span>{image.original_filename}</span>
                <small>
                  {PHASE_LABEL[image.phase] ?? image.phase} · {image.direction}
                </small>
              </Link>
            );
          })}
        </div>
      )}
    </main>
  );
}
