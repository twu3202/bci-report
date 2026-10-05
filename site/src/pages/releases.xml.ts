import type { APIRoute } from 'astro';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { site } from '../data/site';
import { releases } from '../data/releases';
import { topicCards } from '../data/i18n';

/**
 * /releases.xml — an Atom feed of the release log, one entry per reviewed
 * release, newest first, generated from src/data/releases.ts like /releases/
 * itself. It lets a researcher or an aggregator subscribe to the change log
 * instead of re-reading the page.
 *
 * English only, like the downloads it describes. Each entry links to its place
 * on /releases/, to the pages it added, and to every file it ships with that
 * file's size and the SHA-256 of the served bytes — computed at build time from
 * public/data, as the releases page does, so the feed cannot list a hash for a
 * file the site does not serve. Dates are release dates at 00:00 UTC: a release
 * is a day, not a moment.
 */
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const stamp = (date: string) => `${date}T00:00:00Z`;
const facts = (file: string) => {
  const bytes = readFileSync(resolve('public/data', file));
  return { file, length: bytes.length, sha: createHash('sha256').update(bytes).digest('hex') };
};
const typeOf = (file: string) => (file.endsWith('.csv') ? 'text/csv' : 'application/json');
// Since 2026-10-04 a release can name a hub (the v9 rows: every protocol page, the method pages),
// titled as releases.astro titles them.
const hubName: Record<string, string> = { '/protocols/': 'Protocols', '/methods/': 'Methods', '/datasets/': 'Datasets' };
const pageName = (p: string) => {
  const slug = p.match(/^\/topics\/([^/]+)\//)?.[1];
  if (slug) return topicCards.en[slug].title;
  if (hubName[p]) return hubName[p];
  if (p !== '/') throw new Error(`releases.xml.ts: no title for the page ${p}`);
  return 'Core matrix (home page)';
};

export const GET: APIRoute = ({ site: origin }) => {
  const base = String(origin ?? new URL(site.origin));
  const abs = (p: string) => new URL(p, base).href;
  const entries = releases.map(r => {
    const files = r.files.map(facts);
    const content =
      `<p>${esc(r.summary.en)}</p>` +
      r.notes.map(n => `<p>${esc(n.en)}</p>`).join('') +
      `<p>Pages: ${r.pages.map(p => `<a href="${abs(p)}">${esc(pageName(p))}</a>`).join(' · ')}</p>` +
      `<ul>${files.map(f => `<li><a href="${abs(`/data/${f.file}`)}">${f.file}</a> — ${f.length} bytes, SHA-256 of the file as served <code>${f.sha}</code></li>`).join('')}</ul>`;
    return [
      '  <entry>',
      `    <title>${esc(`${r.id} (${r.date})`)}</title>`,
      `    <id>${abs(`/releases/#${r.id}`)}</id>`,
      `    <link rel="alternate" type="text/html" href="${abs(`/releases/#${r.id}`)}"/>`,
      ...r.pages.map(p => `    <link rel="related" type="text/html" href="${abs(p)}"/>`),
      ...files.map(f => `    <link rel="enclosure" type="${typeOf(f.file)}" length="${f.length}" href="${abs(`/data/${f.file}`)}"/>`),
      `    <published>${stamp(r.date)}</published>`,
      `    <updated>${stamp(r.date)}</updated>`,
      `    <summary>${esc(r.summary.en)}</summary>`,
      `    <content type="html">${esc(content)}</content>`,
      '  </entry>',
    ].join('\n');
  });
  const xml = [
    '<?xml version="1.0" encoding="utf-8"?>',
    '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">',
    `  <title>${esc(site.name)} releases</title>`,
    `  <subtitle>Every reviewed ${esc(site.name)} release: what it added, what it held back, and the SHA-256 of every file it ships, as served.</subtitle>`,
    `  <id>${abs('/releases/')}</id>`,
    `  <link rel="self" type="application/atom+xml" href="${abs('/releases.xml')}"/>`,
    `  <link rel="alternate" type="text/html" hreflang="en" href="${abs('/releases/')}"/>`,
    `  <link rel="alternate" type="text/html" hreflang="zh-Hans" href="${abs('/zh/releases/')}"/>`,
    `  <updated>${stamp(releases[0].date)}</updated>`,
    `  <author><name>${esc(site.name)}</name><uri>${abs('/')}</uri></author>`,
    `  <icon>${abs('/favicon.svg')}</icon>`,
    `  <logo>${abs('/logo.png')}</logo>`,
    '  <rights>Aggregate results CC BY 4.0; the underlying recordings keep their own terms.</rights>',
    ...entries,
    '</feed>',
    '',
  ].join('\n');
  return new Response(xml, { headers: { 'Content-Type': 'application/atom+xml; charset=utf-8' } });
};
