import type { NextConfig } from "next";

// Di produksi, Caddy merutekan /api/* langsung ke Go sebelum menyentuh Next.js.
// Di dev, rewrite ini meniru topologi itu: browser melihat satu origin, jadi
// tidak perlu CORS.
const HELLO_API_URL = process.env.HELLO_API_URL ?? "http://127.0.0.1:8080";

const nextConfig: NextConfig = {
  // Kompresi diserahkan ke Caddy (§4.4). Mematikannya di sini juga mencegah
  // stream SSE ter-buffer oleh gzip.
  compress: false,
  async rewrites() {
    return [
      {
        source: "/api/hello/:path*",
        destination: `${HELLO_API_URL}/api/hello/:path*`,
      },
    ];
  },
};

export default nextConfig;
