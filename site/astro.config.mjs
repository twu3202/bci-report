// @ts-check
import { defineConfig } from 'astro/config';
import { site } from './src/data/site.ts';

// https://astro.build/config
export default defineConfig({
  // Canonical origin comes from src/data/site.ts so the name and the hostname
  // are decided in exactly one place. Trailing-slash behaviour is the host's
  // (Cloudflare static-asset html_handling), so it is left at Astro's default.
  site: site.origin,
});
