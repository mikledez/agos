"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { DIRECTIONS, PHASES } from "@/lib/constants";
import { isSearching, searchQueryString } from "@/lib/search";
import { cn } from "@/lib/utils";
import type { LibrarySearchParams } from "@/lib/types";

const DEBOUNCE_MS = 250;

type LibrarySearchProps = {
  search: LibrarySearchParams;
  /** Where clearing the search goes back to (the current folder). */
  clearHref: string;
};

export function LibrarySearch({ search, clearHref }: LibrarySearchProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [text, setText] = useState(search.q);
  const lastSent = useRef(search.q);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Follow the URL when it changes from elsewhere (back button, clear),
  // but never overwrite what the user is still typing.
  useEffect(() => {
    if (search.q !== lastSent.current) {
      lastSent.current = search.q;
      setText(search.q);
    }
  }, [search.q]);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  function go(next: LibrarySearchParams) {
    if (timer.current) clearTimeout(timer.current);
    lastSent.current = next.q;
    const query = searchQueryString(next);
    const href = isSearching(next) ? `/library?${query}` : clearHref;
    startTransition(() => router.replace(href, { scroll: false }));
  }

  function onType(value: string) {
    setText(value);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(
      () => go({ ...search, q: value }),
      DEBOUNCE_MS,
    );
  }

  function toggle(key: "phase" | "direction", value: string) {
    go({ ...search, q: text, [key]: search[key] === value ? null : value });
  }

  const active = isSearching({ ...search, q: text });

  return (
    <div className="max-w-2xl space-y-3">
      <div className="relative">
        <Search
          aria-hidden="true"
          className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          type="search"
          value={text}
          onChange={(event) => onType(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Escape" && active) {
              setText("");
              go({ q: "", phase: null, direction: null });
            }
          }}
          placeholder="Search folders and images"
          aria-label="Search the library"
          className="h-11 pl-9 pr-10 [&::-webkit-search-cancel-button]:hidden"
        />
        <div className="absolute right-1.5 top-1/2 flex -translate-y-1/2 items-center">
          {pending ? (
            <Loader2
              aria-label="Searching"
              className="mr-2 size-4 animate-spin text-muted-foreground"
            />
          ) : active ? (
            <button
              type="button"
              onClick={() => {
                setText("");
                go({ q: "", phase: null, direction: null });
              }}
              className="flex size-8 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="size-4" />
            </button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filters">
        {PHASES.map((phase) => (
          <Chip
            key={phase.value}
            pressed={search.phase === phase.value}
            onClick={() => toggle("phase", phase.value)}
          >
            {phase.label}
          </Chip>
        ))}
        <span aria-hidden="true" className="mx-1 hidden h-5 w-px bg-border sm:block" />
        {DIRECTIONS.map((direction) => (
          <Chip
            key={direction.value}
            pressed={search.direction === direction.value}
            onClick={() => toggle("direction", direction.value)}
          >
            {direction.label}
          </Chip>
        ))}
      </div>
    </div>
  );
}

function Chip({
  pressed,
  onClick,
  children,
}: {
  pressed: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className={cn(
        "h-8 rounded-full border px-3 text-xs font-medium transition-colors outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
        pressed
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}
