"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { useState, type ChangeEvent } from "react";

type LegResult = {
  hip_angle: number;
  knee_angle: number;
  ankle_angle: number;
  feedback: string;
};

type AnalysisResult = {
  image_id: number;
  session_id: number | null;
  phase: string;
  swing_leg: LegResult;
  stance_leg: LegResult;
  thigh_thigh_angle?: number | null;
  feedback: string;
  annotated_image: string;
  error?: string;
};

const PHASES = [
  { value: "toe_off", label: "Toe Off" },
  { value: "mid_stance", label: "Mid Stance" },
  { value: "touchdown", label: "Touchdown" },
];

const DIRECTIONS = [
  { value: "ltr", label: "Running left → right" },
  { value: "rtl", label: "Running right → left" },
];

export default function AnalyzerClient({
  sessionId,
}: {
  sessionId: number | null;
}) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState("toe_off");
  const [direction, setDirection] = useState("ltr");

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("phase", phase);
      formData.append("direction", direction);
      if (sessionId !== null) formData.append("session_id", String(sessionId));

      const res = await fetch("/api/backend/analyze", {
        method: "POST",
        body: formData,
      });
      let data: unknown;
      try {
        data = await res.json();
      } catch {
        throw new Error("Invalid server response");
      }
      if (!res.ok) {
        const d = data as { detail?: string; error?: string };
        setResult({
          ...(data as object),
          error: d.detail || d.error || "Request failed",
        } as AnalysisResult);
      } else {
        setResult(data as AnalysisResult);
      }
    } catch (err) {
      setResult({
        error: err instanceof Error ? err.message : "Upload failed",
      } as AnalysisResult);
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  };

  return (
    <main className="main">
      <h1>Sprint Form Analyzer</h1>
      <p>
        <Link href={sessionId ? `/sessions?session=${sessionId}` : "/sessions"}>
          ← Back to library
        </Link>
      </p>

      <div className="mb-4">
        <label htmlFor="phase">Sprint Phase: </label>
        <select
          id="phase"
          value={phase}
          onChange={(e) => {
            setPhase(e.target.value);
            setResult(null);
          }}
          disabled={loading}
        >
          {PHASES.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-4">
        <label htmlFor="direction">Running Direction: </label>
        <select
          id="direction"
          value={direction}
          onChange={(e) => {
            setDirection(e.target.value);
            setResult(null);
          }}
          disabled={loading}
        >
          {DIRECTIONS.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      </div>

      <input type="file" accept="image/*" onChange={handleUpload} />

      {loading && <p>Analyzing...</p>}

      {result && result.error && <p className="error">Error: {result.error}</p>}

      {result && !result.error && (
        <div className="results">
          <img src={result.annotated_image} alt="Analyzed pose" />
          <h2>Swing Leg</h2>
          <p>Hip Angle: {result.swing_leg.hip_angle}</p>
          <p>Knee Angle: {result.swing_leg.knee_angle}</p>
          <p>Ankle Angle: {result.swing_leg.ankle_angle}</p>
          <p>Feedback: {result.swing_leg.feedback}</p>

          <h2>Stance Leg</h2>
          <p>Hip Angle: {result.stance_leg.hip_angle}</p>
          <p>Knee Angle: {result.stance_leg.knee_angle}</p>
          <p>Ankle Angle: {result.stance_leg.ankle_angle}</p>
          <p>Feedback: {result.stance_leg.feedback}</p>

          {result.thigh_thigh_angle != null && (
            <p>Thigh Separation Angle: {result.thigh_thigh_angle}</p>
          )}

          <p>Feedback: {result.feedback}</p>

          <p>
            <Link href={`/images/${result.image_id}`}>Open saved analysis →</Link>
          </p>
        </div>
      )}
    </main>
  );
}
