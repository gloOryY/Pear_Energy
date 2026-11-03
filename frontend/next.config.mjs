/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  async rewrites() {
    // Внутри Docker-сети обращаемся к сервису backend:8000
    const backendUrl = process.env.BACKEND_INTERNAL_URL || "http://backend:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;