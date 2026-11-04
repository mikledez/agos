import Link from "next/link";
import { cn } from "@/lib/utils";

export function Wordmark({ className }: { className?: string }) {
  return (
    <Link
      href="/"
      aria-label="AGOS home"
      className={cn(
        "inline-flex rounded-md font-display text-[34px] font-extrabold italic leading-none text-primary outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
        className,
      )}
    >
      ĀGOS
    </Link>
  );
}
