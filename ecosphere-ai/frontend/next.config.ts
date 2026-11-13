import type { NextConfig } from 'next';

// GitHub Pages serves project repositories under /<repository-name>/.
// Keep local development and standalone hosting at the site root.
const isGitHubPages = process.env.GITHUB_PAGES === 'true';
const repository = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'EcoSphere-AI';
const basePath = repository.endsWith('.github.io') ? '' : `/${repository}`;

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  ...(isGitHubPages
    ? {
        output: 'export' as const,
        basePath,
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {}),
};

export default nextConfig;
