import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Keep Turbopack scoped to client/ in this monorepo (avoids watching .venv, server/, etc.)
  turbopack: {
    root: path.resolve(__dirname),
  },
  // Allow HMR/dev resources when app is opened via 127.0.0.1.
  allowedDevOrigins: ["127.0.0.1"],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "i.scdn.co",
        pathname: "/image/**",
      },
    ],
  },
};

export default nextConfig;
