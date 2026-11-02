import { signIn } from "@/auth";

async function signInWithGoogle() {
  "use server";
  await signIn("google", { redirectTo: "/analyzer" });
}

async function signInWithDev(formData: FormData) {
  "use server";
  const email = String(formData.get("email") ?? "");
  await signIn("dev", { email, redirectTo: "/analyzer" });
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  const devLogin = process.env.AUTH_DEV_LOGIN === "1";

  return (
    <main className="main">
      <div className="login">
        <h1>Log in</h1>
        <p>Use your Google account to save and review your sprint analyses.</p>

        <form action={signInWithGoogle}>
          <button type="submit" className="btn login-btn">
            Continue with Google
          </button>
        </form>

        {error && <p className="error">Sign in failed. Please try again.</p>}

        {devLogin && (
          <form action={signInWithDev} className="dev-login">
            <h2>Development login</h2>
            <label htmlFor="dev-email">Email</label>
            <input
              className="email_field"
              id="dev-email"
              name="email"
              type="email"
              required
            />
            <button type="submit" className="btn">
              Continue (dev)
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
