/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone", // Required for Docker multi-stage build (copies only needed files)
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "image.tmdb.org",
        pathname: "/t/p/**",
      },
    ],
    formats: ["image/avif", "image/webp"],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts"],
  },
};

module.exports = nextConfig;
