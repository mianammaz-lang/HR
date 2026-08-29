/** @type {import('next').NextConfig} */
const nextConfig = {
  // On Vercel, /api/* is routed to the Python serverless function by vercel.json
  // Locally, the rewrite proxies /api/* to localhost:8000
  async rewrites() {
    // Only add proxy rewrite when running locally (no NEXT_PUBLIC_API_URL set)
    if (!process.env.NEXT_PUBLIC_API_URL) {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ];
    }
    return [];
  },
  images: {
    domains: ['localhost'],
  },
};

module.exports = nextConfig;
