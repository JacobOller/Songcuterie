import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Keep Turbopack scoped to client/ in this monorepo (avoids watching .venv, server/, etc.)
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
