import path from "node:path";
import type { NextConfig } from "next";

/** npm workspaces hoist `next` to the monorepo root — Turbopack must see that tree. */
const monorepoRoot = path.join(__dirname, "..", "..");

const nextConfig: NextConfig = {
  transpilePackages: [
    "@daifend/types",
    "@daifend/sdk",
    "@daifend/config",
    "@daifend/security",
    "@daifend/telemetry",
  ],
  turbopack: {
    root: monorepoRoot,
  },
  async headers() {
    const csp = [
      "default-src 'self'",
      "base-uri 'self'",
      "frame-ancestors 'none'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      "style-src 'self' 'unsafe-inline'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "connect-src 'self' http://127.0.0.1:* http://localhost:* ws://127.0.0.1:* ws://localhost:*",
    ].join("; ");
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
