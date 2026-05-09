import { NextResponse, type NextRequest } from "next/server";
import { daifendSecurityHeaders } from "@daifend/security";

export function middleware(request: NextRequest) {
  void request;
  const res = NextResponse.next();
  const headers = daifendSecurityHeaders();
  for (const [k, v] of Object.entries(headers)) {
    res.headers.set(k, v);
  }
  return res;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|icon.svg|brand/).*)",
  ],
};
