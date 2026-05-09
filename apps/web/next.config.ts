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
};

export default nextConfig;
