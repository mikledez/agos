import { SignJWT } from "jose";
import type { Session } from "next-auth";

export async function mintBackendToken(
  user: Session["user"],
): Promise<string> {
  const secret = process.env.AGOS_INTERNAL_SECRET;
  if (!secret) {
    throw new Error("AGOS_INTERNAL_SECRET is not configured");
  }
  if (!user?.email) {
    throw new Error("Cannot mint a backend token without an email");
  }

  return new SignJWT({
    email: user.email,
    name: user.name ?? null,
    picture: user.image ?? null,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(user.email)
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(new TextEncoder().encode(secret));
}
