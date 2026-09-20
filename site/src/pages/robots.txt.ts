import type { APIRoute } from 'astro';
import { site } from '../data/site';

// Generated rather than static so the hostname follows src/data/site.ts.
export const GET: APIRoute = ({ site: origin }) => {
  const base = (origin ?? new URL(site.origin)).href.replace(/\/$/, '');
  return new Response(
    `# ${site.name} — a personal, noncommercial research preview.\n` +
    `# Crawling the published aggregate results and methods is fine.\n` +
    `User-agent: *\nAllow: /\nDisallow: /404.html\n\n` +
    `Sitemap: ${base}/sitemap.xml\n`,
    { headers: { 'Content-Type': 'text/plain; charset=utf-8' } },
  );
};
