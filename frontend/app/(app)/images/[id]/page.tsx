/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { backendAssetUrl, backendFetch } from "@/lib/backend";
import { deleteImage, generateHumanization } from "../actions";

type Image = {
  id: number;
  session_id: number | null;
  original_filename: string;
  phase: string;
  direction: string;
  swing_hip: number | null;
  swing_knee: number | null;
  swing_ankle: number | null;
  stance_hip: number | null;
  stance_knee: number | null;
  stance_ankle: number | null;
  thigh_thigh: number | null;
  feedback: string | null;
  swing_feedback: string | null;
  stance_feedback: string | null;
  original_url: string;
  annotated_url: string | null;
};

type Humanization = {
  model: string;
  humanized_text: string;
};

type ImageDetail = {
  image: Image;
  humanization: Humanization | null;
};

function angle(value: number | null): string {
  return value == null ? "—" : `${value}°`;
}

export default async function ImagePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const [{ id }, { error }] = await Promise.all([params, searchParams]);

  const response = await backendFetch(`/images/${id}`);
  if (response.status === 401) redirect("/login");
  if (response.status === 404) notFound();
  if (!response.ok) {
    throw new Error(`Backend request failed (${response.status})`);
  }

  const detail = (await response.json()) as ImageDetail;
  const { image, humanization } = detail;
  const src =
    backendAssetUrl(image.annotated_url ?? image.original_url) ?? undefined;

  return (
    <main className="main">
      <h1>{image.original_filename}</h1>
      <p className="library-nav">
        <Link href="/sessions">Library</Link>
        {image.session_id ? (
          <>
            {" / "}
            <Link href={`/sessions?session=${image.session_id}`}>Session</Link>
          </>
        ) : null}
      </p>

      <img className="detail-image" src={src} alt={image.original_filename} />

      <p>
        {image.phase.replace("_", " ")} · {image.direction}
      </p>

      <table className="angles">
        <thead>
          <tr>
            <th>Leg</th>
            <th>Hip</th>
            <th>Knee</th>
            <th>Ankle</th>
            <th>Feedback</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Swing</td>
            <td>{angle(image.swing_hip)}</td>
            <td>{angle(image.swing_knee)}</td>
            <td>{angle(image.swing_ankle)}</td>
            <td>{image.swing_feedback ?? "—"}</td>
          </tr>
          <tr>
            <td>Stance</td>
            <td>{angle(image.stance_hip)}</td>
            <td>{angle(image.stance_knee)}</td>
            <td>{angle(image.stance_ankle)}</td>
            <td>{image.stance_feedback ?? "—"}</td>
          </tr>
        </tbody>
      </table>

      {image.thigh_thigh != null && (
        <p>Thigh separation: {angle(image.thigh_thigh)}</p>
      )}
      <p>Overall: {image.feedback ?? "—"}</p>

      <section className="humanization">
        <h2>Coach feedback</h2>
        {error && <p className="error">{error}</p>}
        {humanization ? (
          <>
            <p>{humanization.humanized_text}</p>
            <small>Model: {humanization.model}</small>
          </>
        ) : (
          <p>No coach feedback generated yet.</p>
        )}
        <form action={generateHumanization} className="inline-form">
          <input type="hidden" name="image_id" value={image.id} />
          <button type="submit" className="btn">
            {humanization ? "Regenerate feedback" : "Generate feedback"}
          </button>
        </form>
      </section>

      <form action={deleteImage} className="inline-form">
        <input type="hidden" name="image_id" value={image.id} />
        <button type="submit" className="btn danger">
          Delete image
        </button>
      </form>
    </main>
  );
}
