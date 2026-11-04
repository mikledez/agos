"use client";

import Link from "next/link";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function AppError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto flex max-w-screen-2xl flex-col items-center px-4 py-24 text-center sm:px-6 lg:px-8">
      <p className="label-caps text-primary">Something went wrong</p>
      <h1 className="display-type mt-2 text-4xl sm:text-5xl">
        This page could not load
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Try again, or go back home.
      </p>
      <div className="mt-6 flex gap-2">
        <Button type="button" onClick={() => unstable_retry()}>
          Try again
        </Button>
        <Button asChild variant="outline">
          <Link href="/">Go home</Link>
        </Button>
      </div>
    </div>
  );
}
