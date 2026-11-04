import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/app-shell";

export default function NotFound() {
  return (
    <AppShell>
      <div className="mx-auto flex max-w-screen-2xl flex-col items-center px-4 py-24 text-center sm:px-6 lg:px-8">
        <p className="label-caps text-primary">404</p>
        <h1 className="mt-2 display-type text-4xl sm:text-5xl">
          Page not found
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          This page does not exist or has moved.
        </p>
        <Button asChild className="mt-6">
          <Link href="/">Go home</Link>
        </Button>
      </div>
    </AppShell>
  );
}
