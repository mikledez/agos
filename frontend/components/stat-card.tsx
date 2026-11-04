import type { ReactNode } from "react";

type StatCardProps = {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
};

export function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className="rounded-lg border border-border border-t-2 border-t-primary bg-card px-4 py-3.5">
      <dt className="label-caps text-muted-foreground">{label}</dt>
      <dd className="mt-1.5 font-display text-4xl font-bold leading-none tabular-nums">{value}</dd>
      {hint ? (
        <dd className="mt-0.5 text-xs text-muted-foreground">{hint}</dd>
      ) : null}
    </div>
  );
}
