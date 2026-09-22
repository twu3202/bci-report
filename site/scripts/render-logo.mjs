// Rasterize public/logo.svg to a transparent square PNG on stdout.
// Pillow cannot read SVG, so generate-brand-assets.py calls this for the
// pixels and does the composing itself. sharp is already a dependency of the
// site build; nothing extra is installed.
//
//     node scripts/render-logo.mjs 1024 > logo.png
import sharp from 'sharp';
import { readFileSync } from 'node:fs';

const size = Number(process.argv[2] ?? 1024);
const svg = readFileSync(new URL('../public/logo.svg', import.meta.url));
const png = await sharp(svg, { density: 72 * size / 376 }).resize(size, size).png().toBuffer();
process.stdout.write(png);
