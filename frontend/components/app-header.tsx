import Link from "next/link";
import { Activity } from "lucide-react";
import { auth } from "@/auth";
import { Button } from "@/components/ui/button";
import { MainNav } from "@/components/main-nav";
import { UserMenu } from "@/components/user-menu";

export async function AppHeader() {
  const session = await auth();
  const user = session?.user;

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-2 px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-lg font-semibold tracking-tight"
          aria-label="AGOS home"
        >
          <span className="flex size-8 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <Activity className="size-4" aria-hidden="true" />
          </span>
          <span className="text-lg sm:text-xl">AGOS</span>
        </Link>

        <div className="flex items-center gap-1 sm:gap-3">
          <MainNav />
          {user?.email ? (
            <UserMenu
              name={user.name ?? null}
              email={user.email}
              image={user.image ?? null}
            />
          ) : (
            <Button asChild size="sm" className="rounded-full px-4">
              <Link href="/login">Login</Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
