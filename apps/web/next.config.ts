import path from "node:path";
import type { NextConfig } from "next";

// Di container dan VPS, Caddy merutekan /api/* langsung ke Go sebelum
// menyentuh Next.js. Di `next dev`, rewrite di bawah meniru topologi itu
// sehingga browser melihat satu origin dan CORS tidak diperlukan.
const HELLO_API_URL = process.env.HELLO_API_URL ?? "http://127.0.0.1:8080";

const nextConfig: NextConfig = {
  // Kompresi diserahkan ke Caddy (§4.4). Mematikannya di sini juga mencegah
  // stream SSE ter-buffer oleh gzip.
  compress: false,
  // Bundle mandiri: server.js + hanya file node_modules yang benar-benar dipakai.
  output: "standalone",
  // Akar monorepo, supaya file tracing menemukan dependensi pnpm di root.
  outputFileTracingRoot: path.join(__dirname, "..", ".."),
  async rewrites() {
    // rewrites dibekukan saat `next build`, jadi tidak bisa diatur lewat env
    // runtime. Karena itu rewrite hanya aktif di `next dev` (LAB-ADR-012).
    if (process.env.NODE_ENV !== "development") {
      return [];
    }
    return [
      {
        source: "/api/hello/:path*",
        destination: `${HELLO_API_URL}/api/hello/:path*`,
      },
    ];
  },
};

export default nextConfig;
