import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE, verifySession } from "@/lib/session";

export async function proxy(request: NextRequest) {
    const path = request.nextUrl.pathname;
    const token = request.cookies.get(SESSION_COOKIE)?.value;
    const session = await verifySession(token);

    if (path.startsWith("/analyzer") && !session) {
        return NextResponse.redirect(new URL("/login", request.url));
    }
    if (path==="/login" && session) {
        return NextResponse.redirect(new URL("/analyzer", request.url));
    }
    return NextResponse.next();
}

export const config = {
    matcher: ["/analyzer/:path*", "/login"],
};