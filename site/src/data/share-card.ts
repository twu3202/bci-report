/**
 * The share card every page points `og:image` at: public/og.png.
 *
 * scripts/generate-brand-assets.py draws it, with the core matrix's counts read
 * from mvp.json, and records the file's SHA-256, size, text and counts in
 * scripts/brand-assets.json. The counts here are derived the same way, so the
 * alt text says what the picture says; check-workbench.mjs compares the
 * recorded counts with these and the recorded hash with the served file.
 */
import data from './mvp.json';
import { chrome, type Locale, type ShareCounts } from './i18n';

export const shareCounts: ShareCounts = {
  protocols: data.coverage.displayedProtocols,
  datasets: new Set(data.tracks.map(t => t.dataset)).size,
  comparisons: data.coverage.displayedComparisons,
  methods: new Set(data.tracks.flatMap(t => t.rows.map(r => r.name))).size,
};

export const shareCard = {
  path: '/og.png',
  width: 1200,
  height: 630,
  type: 'image/png',
  alt: (locale: Locale) => chrome[locale].shareAlt(shareCounts),
} as const;
