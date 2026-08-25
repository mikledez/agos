"use client";
import "./globals.css";
import { useState, ChangeEvent } from "react";

type LegResult = {
  hip_angle: number;
  knee_angle: number;
  ankle_angle: number;
  feedback: string;
};

type AnalysisResult = {
  phase: string;
  swing_leg: LegResult;
  stance_leg: LegResult;
  thigh_thigh_angle?: number;
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

export default function Home() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState("toe_off");
  const [direction, setDirection] = useState("ltr");

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("phase", phase);
    formData.append("direction", direction);

    const res = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      setResult({ ...data, error: data.detail || data.error || "Request failed" } as AnalysisResult);
    } else {
      setResult(data as AnalysisResult);
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>Sprint Form Analyzer</h1>

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

      <input type="file" onChange={handleUpload} />

      {loading && <p>Analyzing...</p>}

      {result && result.error && <p>Error: {result.error}</p>}

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

          {result.thigh_thigh_angle !== undefined && (
            <p>Thigh Separation Angle: {result.thigh_thigh_angle}</p>
          )}

          <p>Feedback: {result.feedback}</p>
        </div>
      )}
    </div>
  );
}
