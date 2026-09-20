// @ts-check
import { defineConfig } from 'astro/config';
import { site } from './src/data/site.ts';

// https://astro.build/config
export default defineConfig({
  // Canonical origin comes from src/data/site.ts so the name and the hostname
  // are decided in exactly one place. Trailing-slash behaviour is the host's
  // (Cloudflare static-asset html_handling), so it is left at Astro's default.
  site: site.origin,
  build: {
    // Never inline CSS into the HTML. Astro's default inlines small
    // stylesheets, and a <style> block is exactly what forces
    // `style-src 'unsafe-inline'` in the Content-Security-Policy that
    // public/_headers ships. One extra same-origin request buys a policy with
    // no inline escape hatch at all.
    inlineStylesheets: 'never',
  },
});
