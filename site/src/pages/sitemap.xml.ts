import type { APIRoute } from 'astro';
import { site } from '../data/site';

const PAGES = [
  { path: '/', priority: '1.0' },
  { path: '/topics/dry-vs-wet/', priority: '0.8' },
  { path: '/topics/on-the-move/', priority: '0.8' },
  { path: '/topics/calibration-budget/', priority: '0.8' },
  { path: '/topics/does-pretraining-help/', priority: '0.8' },
  { path: '/data-use/', priority: '0.5' },
];

export const GET: APIRoute = ({ site: origin }) => {
  const base = (origin ?? new URL(site.origin)).href.replace(/\/$/, '');
  const urls = PAGES.map(
    (p) => `  <url><loc>${base}${p.path}</loc><changefreq>monthly</changefreq>` +
           `<priority>${p.priority}</priority></url>`).join('\n');
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
    { headers: { 'Content-Type': 'application/xml; charset=utf-8' } },
  );
};
