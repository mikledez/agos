"use client";
import "./globals.css";
import { useState, ChangeEvent } from "react";

type AnalysisResult = {
  knee_angle: number;
  hip_angle: number;
  ankle_angle: number;
  feedback: string;
  annotated_image: string;
};

export default function Home() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      body: formData,
    });

    const data: AnalysisResult = await res.json();
    setResult(data);
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>Sprint Form Analyzer</h1>
      <input type="file" onChange={handleUpload} />

      {loading && <p>Analyzing...</p>}

      {result && (
        <div className="results">
          <img src={result.annotated_image} alt="Analyzed pose" />
          <p>Hip Angle: {result.hip_angle}</p>
          <p>Knee Angle: {result.knee_angle}</p>
          <p>Ankle Angle: {result.ankle_angle}</p>
          <p>Feedback: {result.feedback}</p>
        </div>
      )}
    </div>
  );
}