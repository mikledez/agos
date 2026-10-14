import { SignJWT, jwtVerify } from "jose";

export const SESSION_COOKIE = "sessions";
const encodedKey = new TextEncoder().encode(process.env.SESSION_SECRET);

export async function createSession(email:string) {
    return new SignJWT({ email })
    .setProtectedHeader({ alg: "HS256"})
    .setIssuedAt()
    .setExpirationTime("7d")
    .sign(encodedKey);
}

export async function verifySession(token: string | undefined) {
    if (!token) return null;
    try {
        const {payload} = await jwtVerify(token, encodedKey, { algorithms: ["HS256"]});
        return payload;
    } catch {
        return null;
    }
}