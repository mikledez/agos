import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import type { Provider } from "next-auth/providers";

const providers: Provider[] = [Google];

if (process.env.AUTH_DEV_LOGIN === "1") {
  providers.push(
    Credentials({
      id: "dev",
      name: "Development login",
      credentials: {
        email: { label: "Email", type: "email" },
      },
      authorize(credentials) {
        const email =
          typeof credentials?.email === "string" ? credentials.email : "";
        if (!email.trim()) return null;
        return { id: email, email: email.trim(), name: "Dev User" };
      },
    }),
  );
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers,
  pages: { signIn: "/login" },
  session: { strategy: "jwt" },
});
