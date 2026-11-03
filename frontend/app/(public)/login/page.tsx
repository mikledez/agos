import Link from "next/link";
import { Activity, ArrowLeft } from "lucide-react";
import { signIn } from "@/auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

async function signInWithGoogle() {
  "use server";
  await signIn("google", { redirectTo: "/library" });
}

async function signInWithDev(formData: FormData) {
  "use server";
  const email = String(formData.get("email") ?? "");
  await signIn("dev", { email, redirectTo: "/library" });
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  const devLogin = process.env.AUTH_DEV_LOGIN === "1";

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col items-center px-4 py-12 sm:px-6 sm:py-20 lg:px-8">
      <div className="w-full max-w-md">
        <Link
          href="/"
          className="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back home
        </Link>

        <Card className="border-border/80 shadow-lg shadow-primary/5">
          <CardHeader className="text-center">
            <span className="mx-auto mb-2 flex size-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
              <Activity className="size-6" aria-hidden="true" />
            </span>
            <CardTitle className="text-2xl">Log in to AGOS</CardTitle>
            <CardDescription>
              Use your Google account to save and review your sprint analyses.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <form action={signInWithGoogle}>
              <Button
                type="submit"
                size="lg"
                className="h-11 w-full rounded-full"
              >
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
              <form action={signInWithDev} className="space-y-3 border-t pt-5">
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
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
