import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep Turbopack scoped to apps/web (not the whole monorepo — that caused 60–90s page loads).
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
