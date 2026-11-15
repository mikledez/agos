"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PHASE_LABEL } from "@/lib/constants";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { AthleteProgress, ProgressPoint } from "@/lib/types";

type Datum = { label: string; date: string; value: number | null; note?: string };

type TrendChartProps = {
  title: string;
  data: Datum[];
  band?: [number, number];
  unit: string;
  fixedDomain?: [number, number];
  height?: number;
};

const DEFAULT_WIDTH = 320;
const PAD = { top: 12, right: 12, bottom: 22, left: 34 };

function niceTicks(lo: number, hi: number, count = 3): number[] {
  const span = hi - lo || 1;
  const raw = span / count;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step =
    [1, 2, 5, 10].map((m) => m * magnitude).find((s) => s >= raw) ?? raw;
  const ticks: number[] = [];
  for (let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) {
    ticks.push(Math.round(t * 100) / 100);
  }
  return ticks;
}

function domainFor(
  values: number[],
  band?: [number, number],
  fixed?: [number, number],
): [number, number] {
  if (fixed) return fixed;
  const all = [...values, ...(band ?? [])];
  if (all.length === 0) return [0, 1];
  const min = Math.min(...all);
  const max = Math.max(...all);
  const pad = Math.max((max - min) * 0.15, 3);
  return [Math.floor(min - pad), Math.ceil(max + pad)];
}

function bandStatus(value: number, band?: [number, number]) {
  if (!band) return null;
  if (value < band[0]) return "Below target";
  if (value > band[1]) return "Above target";
  return "In target range";
}

/** Single-series line over upload order, with an optional target band. */
function TrendChart({
  title,
  data,
  band,
  unit,
  fixedDomain,
  height = 150,
}: TrendChartProps) {
  const [hover, setHover] = useState<number | null>(null);
  // Draw at the real pixel width so text and line weights never get stretched.
  const boxRef = useRef<HTMLDivElement>(null);
  const [WIDTH, setWidth] = useState(DEFAULT_WIDTH);
  useEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.max(200, Math.round(entry.contentRect.width)));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const values = data.flatMap((d) => (d.value == null ? [] : [d.value]));

  const [lo, hi] = domainFor(values, band, fixedDomain);

  const plotW = WIDTH - PAD.left - PAD.right;
  const plotH = height - PAD.top - PAD.bottom;
  const x = (i: number) =>
    PAD.left + (data.length === 1 ? plotW / 2 : (i / (data.length - 1)) * plotW);
  const y = (v: number) => PAD.top + (1 - (v - lo) / (hi - lo)) * plotH;

  // Break the line at missing measurements instead of bridging them.
  const segments: string[] = [];
  let current = "";
  data.forEach((d, i) => {
    if (d.value == null) {
      if (current) segments.push(current);
      current = "";
      return;
    }
    current += `${current ? "L" : "M"}${x(i).toFixed(1)},${y(d.value).toFixed(1)}`;
  });
  if (current) segments.push(current);

  function onPointerMove(event: React.PointerEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const px = ((event.clientX - rect.left) / rect.width) * WIDTH;
    let best = 0;
    data.forEach((_, i) => {
      if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i;
    });
    setHover(best);
  }

  const hovered = hover != null ? data[hover] : null;
  const latest = [...data].reverse().find((d) => d.value != null);

  return (
    <figure className="rounded-lg border border-border bg-card p-3">
      <figcaption className="flex items-baseline justify-between gap-2 px-1">
        <span className="text-sm font-semibold">{title}</span>
        <span className="text-xs tabular-nums text-muted-foreground">
          {latest?.value != null ? `Latest ${Math.round(latest.value)}${unit}` : "Not measured"}
        </span>
      </figcaption>
      <div ref={boxRef} className="relative mt-1">
        <svg
          viewBox={`0 0 ${WIDTH} ${height}`}
          width={WIDTH}
          height={height}
          className="block max-w-full touch-none select-none"
          role="img"
          aria-label={`${title}: ${values.length} measurements${
            band ? `, target ${band[0]} to ${band[1]}${unit}` : ""
          }`}
          onPointerMove={onPointerMove}
          onPointerLeave={() => setHover(null)}
        >
          {niceTicks(lo, hi).map((t) => (
            <g key={t}>
              <line
                x1={PAD.left}
                x2={WIDTH - PAD.right}
                y1={y(t)}
                y2={y(t)}
                stroke="var(--border)"
                strokeWidth={1}
              />
              <text
                x={PAD.left - 6}
                y={y(t)}
                dy="0.32em"
                textAnchor="end"
                className="fill-muted-foreground text-[10px] tabular-nums"
              >
                {t}
              </text>
            </g>
          ))}
          {band ? (
            <rect
              x={PAD.left}
              width={plotW}
              y={y(band[1])}
              height={Math.max(1, y(band[0]) - y(band[1]))}
              fill="var(--chart-target)"
              fillOpacity={0.12}
            />
          ) : null}
          {hovered ? (
            <line
              x1={x(hover!)}
              x2={x(hover!)}
              y1={PAD.top}
              y2={PAD.top + plotH}
              stroke="var(--muted-foreground)"
              strokeWidth={1}
            />
          ) : null}
          {segments.map((d, i) => (
            <path
              key={i}
              d={d}
              fill="none"
              stroke="var(--primary)"
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ))}
          {data.map((d, i) =>
            d.value == null ? null : (
              <circle
                key={i}
                cx={x(i)}
                cy={y(d.value)}
                r={hover === i ? 5.5 : 4}
                fill="var(--primary)"
                stroke="var(--card)"
                strokeWidth={2}
              />
            ),
          )}
          <text
            x={PAD.left}
            y={height - 6}
            className="fill-muted-foreground text-[10px]"
          >
            {data[0]?.date}
          </text>
          {data.length > 1 ? (
            <text
              x={WIDTH - PAD.right}
              y={height - 6}
              textAnchor="end"
              className="fill-muted-foreground text-[10px]"
            >
              {data[data.length - 1].date}
            </text>
          ) : null}
        </svg>
        {hovered ? (
          <div
            className="pointer-events-none absolute top-0 z-10 w-max max-w-[12rem] -translate-x-1/2 rounded-md border border-border bg-popover px-2.5 py-1.5 text-xs shadow-md"
            style={{
              left: `${Math.min(80, Math.max(20, (x(hover!) / WIDTH) * 100))}%`,
            }}
          >
            <p className="truncate font-medium">{hovered.label}</p>
            <p className="text-muted-foreground">{hovered.date}</p>
            <p className="mt-0.5 tabular-nums">
              {hovered.value == null
                ? "Not measured"
                : `${Math.round(hovered.value)}${unit}`}
              {hovered.value != null && bandStatus(hovered.value, band)
                ? ` · ${bandStatus(hovered.value, band)}`
                : ""}
            </p>
            {hovered.note ? (
              <p className="text-muted-foreground">{hovered.note}</p>
            ) : null}
          </div>
        ) : null}
      </div>
      {band ? (
        <p className="mt-1 flex items-center gap-1.5 px-1 text-xs text-muted-foreground">
          <span
            aria-hidden="true"
            className="inline-block size-2.5 rounded-sm"
            style={{ background: "var(--chart-target)", opacity: 0.35 }}
          />
          Target {band[0]}–{band[1]}
          {unit}
        </p>
      ) : null}
    </figure>
  );
}

const JOINTS = ["hip", "knee", "ankle"] as const;
const JOINT_LABEL = { hip: "Hip", knee: "Knee", ankle: "Ankle" } as const;

function scoreNote(point: ProgressPoint) {
  return `${point.in_range} of ${point.measured} joints in range · ${
    PHASE_LABEL[point.phase] ?? point.phase
  }`;
}

export function AthleteProgressPanel({
  progress,
  className,
}: {
  progress: AthleteProgress;
  className?: string;
}) {
  const { points, ranges } = progress;
  const phases = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of points) counts.set(p.phase, (counts.get(p.phase) ?? 0) + 1);
    return Object.keys(ranges).filter((phase) => counts.has(phase));
  }, [points, ranges]);
  const busiest = useMemo(
    () =>
      phases.reduce<string | null>(
        (best, phase) =>
          best == null ||
          points.filter((p) => p.phase === phase).length >
            points.filter((p) => p.phase === best).length
            ? phase
            : best,
        null,
      ),
    [phases, points],
  );
  const [phase, setPhase] = useState<string | null>(busiest);
  const [showTable, setShowTable] = useState(false);

  if (points.length === 0) {
    return (
      <section className={cn("rounded-lg border border-dashed border-border p-6", className)}>
        <h2 className="label-caps text-muted-foreground">Progress</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Upload photos to this athlete (or its subfolders) and their form will
          be tracked here over time.
        </p>
      </section>
    );
  }

  const scored = points.filter((p) => p.score != null);
  const first = scored[0];
  const last = scored[scored.length - 1];
  const change =
    first && last && scored.length > 1 ? last.score! - first.score! : null;

  const activePhase = phase && phases.includes(phase) ? phase : busiest;
  const phasePoints = points.filter((p) => p.phase === activePhase);
  const phaseRanges = activePhase ? ranges[activePhase] : null;
  const toDatum = (p: ProgressPoint, value: number | null): Datum => ({
    label: p.original_filename,
    date: formatDate(p.created_at),
    value,
  });

  return (
    <section className={cn("space-y-4", className)} aria-labelledby="progress-heading">
      <div>
        <h2 id="progress-heading" className="display-type text-3xl">
          Progress
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Form score is the share of measured joints inside their target range.
          Photos from subfolders are included.
        </p>
      </div>

      <dl className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Analyses"
          value={points.length.toLocaleString()}
          hint={`Since ${formatDate(points[0].created_at)}`}
        />
        <StatCard
          label="Latest form score"
          value={last ? `${last.score}%` : "—"}
          hint={last ? scoreNote(last) : "No joints measured yet"}
        />
        <StatCard
          label="Change"
          value={
            change == null ? "—" : `${change > 0 ? "+" : change < 0 ? "−" : ""}${Math.abs(change)}`
          }
          hint={
            change == null
              ? "Needs two analyses"
              : "Points since the first analysis"
          }
        />
      </dl>

      <TrendChart
        title="Form score"
        unit="%"
        fixedDomain={[0, 100]}
        height={170}
        data={points.map((p) => ({
          ...toDatum(p, p.score),
          note: scoreNote(p),
        }))}
      />

      {activePhase && phaseRanges ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Tabs value={activePhase} onValueChange={setPhase}>
              <TabsList>
                {phases.map((p) => (
                  <TabsTrigger key={p} value={p}>
                    {PHASE_LABEL[p] ?? p}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowTable((v) => !v)}
              aria-expanded={showTable}
            >
              {showTable ? "Show charts" : "Show as table"}
            </Button>
          </div>

          {showTable ? (
            <div className="overflow-x-auto rounded-lg border border-border bg-card">
              <table className="w-full text-sm tabular-nums">
                <thead className="text-left text-xs text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="px-3 py-2 font-medium">Date</th>
                    <th className="px-3 py-2 font-medium">Photo</th>
                    <th className="px-3 py-2 font-medium">Score</th>
                    {JOINTS.map((j) => (
                      <th key={`s-${j}`} className="px-3 py-2 font-medium">
                        Swing {j}
                      </th>
                    ))}
                    {JOINTS.map((j) => (
                      <th key={`t-${j}`} className="px-3 py-2 font-medium">
                        Stance {j}
                      </th>
                    ))}
                    {phaseRanges.thigh_thigh ? (
                      <th className="px-3 py-2 font-medium">Thigh gap</th>
                    ) : null}
                  </tr>
                </thead>
                <tbody>
                  {phasePoints.map((p) => (
                    <tr key={p.image_id} className="border-b border-border last:border-0">
                      <td className="whitespace-nowrap px-3 py-2">{formatDate(p.created_at)}</td>
                      <td className="max-w-[12rem] truncate px-3 py-2">{p.original_filename}</td>
                      <td className="px-3 py-2">{p.score == null ? "—" : `${p.score}%`}</td>
                      {JOINTS.map((j) => (
                        <td key={`s-${j}`} className="px-3 py-2">
                          {p.swing[j] == null ? "—" : `${Math.round(p.swing[j]!)}°`}
                        </td>
                      ))}
                      {JOINTS.map((j) => (
                        <td key={`t-${j}`} className="px-3 py-2">
                          {p.stance[j] == null ? "—" : `${Math.round(p.stance[j]!)}°`}
                        </td>
                      ))}
                      {phaseRanges.thigh_thigh ? (
                        <td className="px-3 py-2">
                          {p.thigh_thigh == null ? "—" : `${Math.round(p.thigh_thigh)}°`}
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {(["swing", "stance"] as const).flatMap((role) =>
                JOINTS.map((joint) => (
                  <TrendChart
                    key={`${role}-${joint}`}
                    title={`${role === "swing" ? "Swing" : "Stance"} ${JOINT_LABEL[joint].toLowerCase()}`}
                    unit="°"
                    band={phaseRanges[role][joint]}
                    data={phasePoints.map((p) => toDatum(p, p[role][joint]))}
                  />
                )),
              )}
              {phaseRanges.thigh_thigh ? (
                <TrendChart
                  title="Thigh gap"
                  unit="°"
                  band={phaseRanges.thigh_thigh}
                  data={phasePoints.map((p) => toDatum(p, p.thigh_thigh))}
                />
              ) : null}
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}
