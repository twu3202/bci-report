import type { APIRoute } from 'astro';
import data from '../data/mvp.json';
import deployment from '../data/deployment-topics.json';
import { site } from '../data/site';
import { alternates, locales, localizePath, translatedPaths } from '../data/i18n';

/**
 * `lastmod` only, taken from the release each page actually renders.
 *
 * Google states it ignores `changefreq` and `priority` outright, and uses
 * `lastmod` when a site reports it honestly. The dates come from the release
 * payloads rather than the build clock, so a rebuild that changes nothing does
 * not tell crawlers the content moved — the fastest way to have `lastmod`
 * ignored is to let it drift.
 *
 * Translated pages list every language version, each carrying the full set of
 * `xhtml:link` alternates including itself. That is the sitemap form of
 * hreflang, and Google requires it to be reciprocal: a Chinese page that points
 * at English is ignored unless English points back.
 */
const RELEASE = data.generatedAt.slice(0, 10);
const TOPICS = deployment.generated_at.slice(0, 10);
const lastmodOf = (path: string) => (path.startsWith('/topics/') ? TOPICS : RELEASE);

export const GET: APIRoute = ({ site: origin }) => {
  const base = String(origin ?? new URL(site.origin));
  const abs = (p: string) => new URL(p, base).href;
  const entries: string[] = [];
  for (const path of translatedPaths) {
    const links = alternates(path, base)
      .map((l) => `<xhtml:link rel="alternate" hreflang="${l.hreflang}" href="${l.href}"/>`).join('');
    for (const code of locales)
      entries.push(`  <url><loc>${abs(localizePath(path, code))}</loc><lastmod>${lastmodOf(path)}</lastmod>${links}</url>`);
  }
  // English-only: no alternates to declare.
  entries.push(`  <url><loc>${abs('/data-use/')}</loc><lastmod>${RELEASE}</lastmod></url>`);
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n` +
    `${entries.join('\n')}\n</urlset>\n`,
    { headers: { 'Content-Type': 'application/xml; charset=utf-8' } },
  );
};
