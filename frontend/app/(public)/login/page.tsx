import { signIn } from "@/auth";
import { PosePreview } from "@/components/pose-preview";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Wordmark } from "@/components/wordmark";

async function signInWithGoogle() {
  "use server";
  await signIn("google", { redirectTo: "/" });
}

async function signInWithDev(formData: FormData) {
  "use server";
  const email = String(formData.get("email") ?? "");
  await signIn("dev", { email, redirectTo: "/" });
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  const devLogin = process.env.AUTH_DEV_LOGIN === "1";

  return (
    <div className="grid min-h-svh lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      <main className="flex flex-col px-4 py-6 sm:px-10 lg:px-16">
        <div>
          <Wordmark />
        </div>
        <div className="flex flex-1 items-center py-10">
          <div className="mx-auto w-full max-w-sm">
            <h1 className="display-type text-5xl">
              Log in to ĀGOS
            </h1>
            <p className="mt-3 text-base text-muted-foreground">
              Use your Google account to save and review your sprint analyses.
            </p>

            <div className="mt-8 space-y-5">
              <form action={signInWithGoogle}>
                <Button type="submit" size="lg" className="w-full">
                  Continue with Google
                </Button>
              </form>

              {error ? (
                <p
                  role="alert"
                  className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive"
                >
                  Sign in failed. Please try again.
                </p>
              ) : null}

              {devLogin ? (
                <form
                  action={signInWithDev}
                  className="space-y-3 border-t pt-5"
                >
                  <div className="space-y-1.5">
                    <p className="text-sm font-semibold">Development login</p>
                    <p className="text-xs text-muted-foreground">
                      Available because AUTH_DEV_LOGIN is enabled.
                    </p>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="dev-email">Email</Label>
                    <Input
                      id="dev-email"
                      name="email"
                      type="email"
                      placeholder="dev@example.com"
                      autoComplete="email"
                      required
                    />
                  </div>
                  <Button type="submit" variant="outline" className="w-full">
                    Continue (dev)
                  </Button>
                </form>
              ) : null}
            </div>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          Your images stay private to your account.
        </p>
      </main>

      <aside className="hidden bg-primary text-primary-foreground lg:flex lg:flex-col lg:justify-center lg:px-14 xl:px-20">
        <div className="max-w-xl py-10">
          <p className="label-caps text-white/75">Sprint form analysis</p>
          <h2 className="display-type mt-3 text-6xl xl:text-7xl">
            Sprint mechanics, measured.
          </h2>
          <div className="mt-8 text-foreground">
            <PosePreview />
          </div>
        </div>
      </aside>
    </div>
  );
}
