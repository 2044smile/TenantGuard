/** @type {import('next').NextConfig} */
const nextConfig = {
  // Docker 컨테이너 내부에서 hot reload 감지
  webpack: (config) => {
    config.watchOptions = {
      poll: 1000,
      aggregateTimeout: 300,
    }
    return config
  },
}

module.exports = nextConfig
