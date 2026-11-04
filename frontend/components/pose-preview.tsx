const LIMB = "color-mix(in srgb, var(--foreground) 30%, var(--card))";

const READINGS = [
  { label: "Hip", value: "146°", range: "141–152°" },
  { label: "Knee", value: "151°", range: "146–156°" },
  { label: "Ankle", value: "101°", range: "97–105°" },
];

function Figure() {
  return (
    <svg
      viewBox="0 0 480 290"
      className="h-auto w-full"
      role="presentation"
      aria-hidden="true"
    >
      <line
        x1="0"
        x2="480"
        y1="272"
        y2="272"
        stroke="var(--foreground)"
        strokeWidth="2"
      />
      {[70, 170, 270, 370].map((x) => (
        <line
          key={x}
          x1={x}
          x2={x}
          y1="272"
          y2="282"
          stroke="var(--foreground)"
          strokeWidth="2"
        />
      ))}

      <g
        fill="none"
        stroke={LIMB}
        strokeWidth="9"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M256 84 L216 116 L190 158" />
        <path d="M256 84 L296 122 L334 96" />
        <path d="M232 160 L176 204 L120 176 L104 196" />
      </g>
      <path
        d="M256 84 L232 160"
        fill="none"
        stroke={LIMB}
        strokeWidth="13"
        strokeLinecap="round"
      />
      <circle cx="268" cy="52" r="18" fill={LIMB} />

      <path
        d="M232 160 L304 196 L322 264 L354 268"
        fill="none"
        stroke="var(--primary)"
        strokeWidth="9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {[
        [232, 160],
        [304, 196],
        [322, 264],
      ].map(([cx, cy]) => (
        <circle
          key={`${cx}-${cy}`}
          cx={cx}
          cy={cy}
          r="8"
          fill="var(--card)"
          stroke="var(--primary)"
          strokeWidth="4"
        />
      ))}
    </svg>
  );
}

export function PosePreview() {
  return (
    <figure className="rounded-lg border border-border bg-card">
      <figcaption className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="label-caps">Touchdown</span>
        <span className="text-xs text-muted-foreground">
          Example stance leg
        </span>
      </figcaption>
      <div className="px-4 pt-4">
        <Figure />
      </div>
      <dl className="grid grid-cols-3 divide-x divide-border border-t border-border">
        {READINGS.map((reading) => (
          <div key={reading.label} className="px-4 py-3">
            <dt className="label-caps text-muted-foreground">
              {reading.label}
            </dt>
            <dd className="mt-1 font-display text-3xl font-bold leading-none tabular-nums">
              {reading.value}
            </dd>
            <dd className="mt-1 text-xs tabular-nums text-muted-foreground">
              Target {reading.range}
            </dd>
          </div>
        ))}
      </dl>
    </figure>
  );
}
