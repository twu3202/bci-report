import type { APIRoute } from 'astro';
import data from '../data/mvp.json';
import deployment from '../data/deployment-topics.json';
import { site } from '../data/site';

/**
 * `lastmod` only, taken from the release each page actually renders.
 *
 * Google states it ignores `changefreq` and `priority` outright, and uses
 * `lastmod` when a site reports it honestly. Emitting the two ignored fields and
 * omitting the one that counts was exactly backwards. The dates come from the
 * release payloads rather than the build clock, so a rebuild that changes
 * nothing does not tell crawlers the content moved — the fastest way to have
 * `lastmod` ignored is to let it drift.
 */
const RELEASE = data.generatedAt.slice(0, 10);
const TOPICS = deployment.generated_at.slice(0, 10);

const PAGES = [
  { path: '/', lastmod: RELEASE },
  ...deployment.topics.map((t) => ({ path: `/topics/${t.id}/`, lastmod: TOPICS })),
  { path: '/data-use/', lastmod: RELEASE },
];

export const GET: APIRoute = ({ site: origin }) => {
  const base = (origin ?? new URL(site.origin)).href.replace(/\/$/, '');
  const urls = PAGES.map(
    (p) => `  <url><loc>${base}${p.path}</loc><lastmod>${p.lastmod}</lastmod></url>`).join('\n');
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
    { headers: { 'Content-Type': 'application/xml; charset=utf-8' } },
  );
};
