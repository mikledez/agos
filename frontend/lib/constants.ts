export const PHASES = [
  { value: "toe_off", label: "Toe off" },
  { value: "mid_stance", label: "Mid stance" },
  { value: "touchdown", label: "Touchdown" },
] as const;

export const DIRECTIONS = [
  { value: "ltr", label: "Left to right" },
  { value: "rtl", label: "Right to left" },
] as const;

export const PHASE_LABEL: Record<string, string> = Object.fromEntries(
  PHASES.map((phase) => [phase.value, phase.label]),
);

export const DIRECTION_LABEL: Record<string, string> = Object.fromEntries(
  DIRECTIONS.map((direction) => [direction.value, direction.label]),
);

export const CHAT_SUGGESTIONS = [
  "What drills could help with this?",
  "How do I fix my hip angle?",
  "Explain this phase simply.",
];
