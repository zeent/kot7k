import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

export default function nextConfig(phase: string): NextConfig {
  const isDevelopment = phase === PHASE_DEVELOPMENT_SERVER;

  return {
    // Local development has a Next server; production is served by Django.
    ...(isDevelopment ? {} : { output: "export" as const }),
    images: {
      unoptimized: !isDevelopment,
    },
  };
}
