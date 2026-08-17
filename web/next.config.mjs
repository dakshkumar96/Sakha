/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Hide the bottom-left "N" badge so it doesn't sit on the stage.
  devIndicators: false,
  // Next 16 blocks /_next/* from 127.0.0.1 when the origin is localhost (and vice versa).
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
