import type { ReactNode } from "react";
import { AppHeader } from "@/components/app-header";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col">
      <a
        href="#main"
        className="sr-only z-50 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground focus:not-sr-only focus:fixed focus:left-3 focus:top-3"
      >
        Skip to content
      </a>
      <AppHeader />
      <main id="main" tabIndex={-1} className="flex-1 outline-none">
        {children}
      </main>
      <footer className="border-t border-border">
        {/* Right padding keeps the text clear of the library's add button. */}
        <div className="mx-auto flex max-w-screen-2xl flex-col gap-1 py-6 pl-4 pr-20 text-xs text-muted-foreground sm:flex-row sm:gap-4 sm:pl-6 lg:pl-8">
          <p>ĀGOS sprint form analysis</p>
          <p>Your images stay private to your account.</p>
        </div>
      </footer>
    </div>
  );
}
