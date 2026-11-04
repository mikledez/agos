import Link from "next/link";
import { auth } from "@/auth";
import { Button } from "@/components/ui/button";
import { MainNav } from "@/components/main-nav";
import { UserMenu } from "@/components/user-menu";
import { Wordmark } from "@/components/wordmark";

export async function AppHeader() {
  const session = await auth();
  const user = session?.user;

  return (
    <header className="sticky top-0 z-40 h-[70px] border-b border-border bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="mx-auto flex h-full max-w-screen-2xl items-center gap-2 px-4 sm:gap-3 sm:px-6 lg:px-8">
        <Wordmark />
        <div className="sm:ml-6">
          <MainNav />
        </div>
        <div className="ml-auto flex items-center gap-2">
          {user?.email ? (
            <UserMenu
              name={user.name ?? null}
              email={user.email}
              image={user.image ?? null}
            />
          ) : (
            <Button asChild>
              <Link href="/login">Login</Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
