// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // Canonical origin, used for canonical + Open Graph URLs.
  // Change this if the site is ever served from a different hostname.
  // Trailing-slash behaviour is decided by the host (Cloudflare static-asset
  // html_handling), not here, so it is deliberately left at Astro's default.
  site: 'https://bciarena.ai',
});
