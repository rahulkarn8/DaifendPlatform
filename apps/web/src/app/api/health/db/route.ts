import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

/**
 * Verifies Prisma can reach Postgres. Skip when DATABASE_URL is unset (UI-only dev).
 */
export async function GET() {
  if (!process.env.DATABASE_URL) {
    return NextResponse.json({ ok: true, prisma: "skipped_no_database_url" });
  }
  try {
    await prisma.$queryRaw`SELECT 1`;
    return NextResponse.json({ ok: true, prisma: "connected" });
  } catch (e) {
    const message = e instanceof Error ? e.message : "unknown_error";
    return NextResponse.json(
      { ok: false, prisma: "error", detail: message },
      { status: 503 },
    );
  }
}
