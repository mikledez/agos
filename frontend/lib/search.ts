import { DIRECTIONS, PHASES } from "@/lib/constants";
import type { LibrarySearchParams } from "@/lib/types";

const PHASE_VALUES = new Set<string>(PHASES.map((phase) => phase.value));
const DIRECTION_VALUES = new Set<string>(DIRECTIONS.map((d) => d.value));

export function parseLibrarySearch(params: {
  q?: string;
  phase?: string;
  direction?: string;
}): LibrarySearchParams {
  return {
    q: (params.q ?? "").slice(0, 200),
    phase: params.phase && PHASE_VALUES.has(params.phase) ? params.phase : null,
    direction:
      params.direction && DIRECTION_VALUES.has(params.direction)
        ? params.direction
        : null,
  };
}

export function isSearching(search: LibrarySearchParams): boolean {
  return Boolean(search.q.trim() || search.phase || search.direction);
}

/** Query string (without "?") for a search; empty when nothing is searched. */
export function searchQueryString(search: LibrarySearchParams): string {
  const params = new URLSearchParams();
  if (search.q.trim()) params.set("q", search.q.trim());
  if (search.phase) params.set("phase", search.phase);
  if (search.direction) params.set("direction", search.direction);
  return params.toString();
}
