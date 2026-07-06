import type { NextConfig } from "next";
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
};
module.exports = {
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: `${API_URL}/api/:path*`,
            },
        ];
    },
};
export default nextConfig;
