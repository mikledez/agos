import { NextResponse } from "next/server";
import { createSession, SESSION_COOKIE} from "@/lib/session";

export async function POST(request: Request) {
    const { email, password } = await request.json();

    if (email !== process.env.AUTH_EMAIL || password !== process.env.AUTH_PASSWORD) {
        return NextResponse.json({ error: "Invalid credentials"}, { status: 401});
    }

    const token = await createSession(email);
    const res = NextResponse.json({ ok: true});
    res.cookies.set(SESSION_COOKIE, token, {
        httpOnly: true,
        secure:process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: 60 * 60 * 24 * 7,
    });
    return res;
}