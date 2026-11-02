import { NextResponse } from "next/server";
import { auth } from "@/auth";

const protectedPrefixes = ["/analyzer", "/sessions", "/images"];

export const proxy = auth((request) => {
  const path = request.nextUrl.pathname;
  const signedIn = Boolean(request.auth?.user);

  if (protectedPrefixes.some((prefix) => path.startsWith(prefix)) && !signedIn) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  if (path === "/login" && signedIn) {
    return NextResponse.redirect(new URL("/analyzer", request.url));
  }
  return NextResponse.next();
});

export const config = {
  matcher: [
    "/analyzer/:path*",
    "/sessions/:path*",
    "/images/:path*",
    "/login",
  ],
};
