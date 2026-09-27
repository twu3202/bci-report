// After `astro build`: a Markdown copy of every page, /llms.txt and /llms-full.txt.
//
// Why: assistants and coding agents that fetch a page get navigation, SVG and
// table markup they have to wade through, and often a truncated context. The
// llms.txt convention (llmstxt.org, v2) gives them an index with one line per
// page, and a Markdown copy at <page>/index.md. Every page links to both in its
// <head> (src/components/AgentLinks.astro).
//
// The copies are made FROM THE BUILT HTML, not from the data: a copy cannot say
// anything its page does not, and check-workbench.mjs confirms every figure on a
// page survives into its copy. What is left out on purpose: navigation, the
// language switcher, SVG plot strips (their values are printed beside them),
// and anything aria-hidden.
import { parse, ELEMENT_NODE, TEXT_NODE } from 'ultrahtml';
import { readFileSync, writeFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const dist = process.argv[2] ?? fileURLToPath(new URL('../dist/', import.meta.url));

// --- HTML → Markdown ----------------------------------------------------------------
const decode = s => s
  .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
  .replace(/&(amp|lt|gt|quot|apos|nbsp);/g, (_, e) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' })[e]);
const cls = n => (n.attributes?.class ?? '').split(/\s+/);
const has = (n, c) => cls(n).includes(c);
const kids = n => (n.children ?? []);
const SKIP = new Set(['script', 'style', 'svg', 'button', 'select', 'option', 'dialog', 'template', 'form', 'input', 'label', 'noscript', 'head']);
const BLOCK = new Set(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'figure', 'figcaption', 'section', 'article',
  'div', 'header', 'footer', 'nav', 'main', 'dl', 'dt', 'dd', 'blockquote', 'pre', 'aside', 'details', 'summary', 'caption']);
const skipped = n => n.type === ELEMENT_NODE && (SKIP.has(n.name) || n.attributes?.['aria-hidden'] === 'true'
  || has(n, 'breadcrumbs') || has(n, 'skip') || has(n, 'lang') || has(n, 'visually-hidden'));

let origin = 'https://bci.report';
const absolute = href => href.startsWith('/') ? origin + href : href;

function inline(nodes) {
  let out = '', prevElement = false;
  for (const n of nodes) {
    if (n.type === TEXT_NODE) { out += decode(n.value).replace(/\s+/g, ' '); prevElement = false; continue; }
    if (n.type !== ELEMENT_NODE || skipped(n)) continue;
    // In-page jump links ("Methods & limits ↓") are navigation, not content.
    if (n.name === 'a' && (n.attributes?.href ?? '').startsWith('#')) continue;
    // Two elements side by side (a figure and its label, two links) are two
    // words, even when CSS alone puts the space between them.
    if (prevElement && out && !/\s$/.test(out)) out += ' ';
    prevElement = true;
    const inner = inline(kids(n));
    switch (n.name) {
      case 'strong': case 'b': out += inner.trim() ? `**${inner.trim()}**` : ''; break;
      case 'em': case 'i': out += inner.trim() ? `*${inner.trim()}*` : ''; break;
      case 'code': out += `\`${inner.trim()}\``; break;
      case 'a': {
        const href = n.attributes?.href ?? '';
        // A card: a link wrapping a heading and a summary becomes
        // "[heading](url): the rest", not one long link.
        const title = find(n, k => /^h[2-4]$/.test(k.name) || k.name === 'strong');
        if (title && clean(inner).length > 80) {
          const label = clean(inline(kids(title)));
          const rest = clean(inner).replace(label, '').replace(/^[\s—·:]+/, '');
          out += `[${label}](${absolute(href)}): ${rest}`;
        } else out += !href ? inner : `[${inner.trim()}](${absolute(href)})`;
        break;
      }
      case 'br': out += ' '; break;
      case 'img': out += n.attributes?.alt ?? ''; break;
      case 'small': out += inner.trim() ? ` — ${inner.trim()}` : ''; break;
      case 'span': out += has(n, 'interval') ? ` (${inner.trim()})` : inner; break;
      default: out += BLOCK.has(n.name) ? ` ${inner} ` : inner;
    }
  }
  return out;
}
const clean = s => s.replace(/\s+/g, ' ').replace(/\s+([,.;:)])/g, '$1').replace(/\(\s+/g, '(').trim();
const cell = n => clean(inline(kids(n))).replace(/\|/g, '\\|');

function table(n) {
  const rows = [];
  let caption = '';
  const walk = x => { for (const k of kids(x)) if (k.type === ELEMENT_NODE) {
    if (k.name === 'caption') caption = clean(inline(kids(k)));
    else if (k.name === 'tr') rows.push(kids(k).filter(c => c.type === ELEMENT_NODE && (c.name === 'th' || c.name === 'td')).map(cell));
    else walk(k);
  } };
  walk(n);
  if (!rows.length) return '';
  const width = Math.max(...rows.map(r => r.length));
  const pad = r => [...r, ...Array(width - r.length).fill('')];
  const [head, ...body] = rows.map(pad);
  return `${caption ? `${caption}\n\n` : ''}| ${head.join(' | ')} |\n| ${head.map(() => '---').join(' | ')} |\n${body.map(r => `| ${r.join(' | ')} |`).join('\n')}\n\n`;
}

function plot(n) {
  // IntervalPlot: each row is label + printed value; the SVG strip is dropped.
  const lines = [];
  const walk = x => { for (const k of kids(x)) if (k.type === ELEMENT_NODE) {
    if (has(k, 'ip-row') && !has(k, 'ip-axis')) {
      const label = kids(k).find(c => c.type === ELEMENT_NODE && has(c, 'ip-label'));
      const value = kids(k).find(c => c.type === ELEMENT_NODE && has(c, 'ip-value'));
      lines.push(`- ${clean(inline(kids(label)))}: ${clean(inline(kids(value)))}`);
    } else if (k.name === 'figcaption') lines.unshift(`${clean(inline(kids(k)))}\n`);
    else walk(k);
  } };
  walk(n);
  return `${lines.join('\n')}\n\n`;
}

function block(nodes) {
  let out = '', run = [];
  const flush = () => { const t = clean(inline(run)); if (t) out += `${t}\n\n`; run = []; };
  // A hero lists its eyebrow before the h1; the copy leads with the h1.
  const ordered = [...nodes].sort((a, b) => (b.name === 'h1') - (a.name === 'h1'));
  for (const n of ordered) {
    if (n.type === TEXT_NODE || (n.type === ELEMENT_NODE && !BLOCK.has(n.name) && !skipped(n))) { run.push(n); continue; }
    if (n.type !== ELEMENT_NODE || skipped(n)) continue;
    flush();
    const m = n.name.match(/^h([1-6])$/);
    if (m) { const t = clean(inline(kids(n))); if (t) out += `${'#'.repeat(Number(m[1]))} ${t}\n\n`; continue; }
    switch (n.name) {
      case 'p': case 'figcaption': case 'caption': case 'summary': { const t = clean(inline(kids(n))); if (t) out += `${t}\n\n`; break; }
      case 'pre': out += `\`\`\`\n${rawText(n).trim()}\n\`\`\`\n\n`; break;
      case 'ul': case 'ol': {
        const items = kids(n).filter(k => k.type === ELEMENT_NODE && k.name === 'li').map(li => `- ${clean(inline(kids(li)))}`);
        if (items.length) out += `${items.join('\n')}\n\n`;
        break;
      }
      case 'dl': {
        const parts = []; let term = '';
        const walk = x => { for (const k of kids(x)) if (k.type === ELEMENT_NODE) {
          if (k.name === 'dt') term = clean(inline(kids(k)));
          else if (k.name === 'dd') parts.push(`- ${term}: ${clean(inline(kids(k)))}`);
          else walk(k);
        } };
        walk(n);
        if (parts.length) out += `${parts.join('\n')}\n\n`;
        break;
      }
      case 'table': out += table(n); break;
      case 'figure': out += has(n, 'interval-plot') ? plot(n) : block(kids(n)); break;
      case 'blockquote': out += block(kids(n)).split('\n').map(l => (l ? `> ${l}` : l)).join('\n'); break;
      default: out += block(kids(n));
    }
  }
  flush();
  return out;
}
// Code blocks keep their line breaks.
function rawText(n) {
  let s = '';
  for (const k of kids(n)) s += k.type === TEXT_NODE ? decode(k.value) : k.type === ELEMENT_NODE ? rawText(k) : '';
  return s;
}

function find(node, pred) {
  for (const k of kids(node)) {
    if (k.type !== ELEMENT_NODE) continue;
    if (pred(k)) return k;
    const hit = find(k, pred);
    if (hit) return hit;
  }
  return null;
}
const meta = (html, re) => decode(html.match(re)?.[1] ?? '');

// --- Pages ----------------------------------------------------------------------------
function htmlFiles(dir) {
  return readdirSync(dir).flatMap(f => {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) return f === '_astro' || f === 'data' ? [] : htmlFiles(p);
    return f === 'index.html' ? [p] : [];
  });
}

const pages = [];
for (const file of htmlFiles(dist)) {
  const html = readFileSync(file, 'utf8');
  const canonical = meta(html, /<link rel="canonical" href="([^"]+)"/);
  origin = new URL(canonical).origin;
  const ast = parse(html);
  const main = find(ast, n => n.name === 'main');
  if (!main) continue;
  const title = meta(html, /<title>([^<]*)<\/title>/);
  const description = meta(html, /<meta name="description" content="([^"]*)"/);
  const lang = meta(html, /<html lang="([^"]+)"/);
  const answer = find(main, n => n.name === 'section' && has(n, 'short-answer'));
  const answerText = answer ? clean(inline(kids(find(answer, n => n.name === 'p')))) : '';
  const h1 = clean(inline(kids(find(main, n => n.name === 'h1') ?? { children: [] })));
  const body = block(kids(main)).replace(/\n{3,}/g, '\n\n').trim();
  const footer = lang === 'zh-Hans'
    ? `---\n本文是 ${canonical} 的 Markdown 版本，由已发布的网页生成。数字均为聚合结果；使用条款见 ${origin}/data-use/（英文）。`
    : `---\nMarkdown copy of ${canonical}, generated from the published page. Figures are aggregate results; terms of use: ${origin}/data-use/`;
  const md = `${body}\n\n${footer}\n`;
  writeFileSync(file.replace(/index\.html$/, 'index.md'), md);
  pages.push({ path: new URL(canonical).pathname, canonical, title, h1, description, answerText, lang, md });
}

// --- llms.txt -----------------------------------------------------------------------------
const en = pages.filter(p => p.lang === 'en');
const mdUrl = p => `${p.canonical}index.md`;
const by = prefix => en.filter(p => p.path.startsWith(prefix) && p.path !== prefix).sort((a, b) => a.path.localeCompare(b.path));
const line = (p, note) => `- [${p.h1}](${mdUrl(p)}): ${note}`;
const home = en.find(p => p.path === '/');
const topicOrder = [...home.md.matchAll(/\]\(https?:\/\/[^/]+(\/topics\/[^/]+\/)\)/g)].map(m => m[1]);
const topics = by('/topics/').sort((a, b) => topicOrder.indexOf(a.path) - topicOrder.indexOf(b.path));
const api = en.find(p => p.path === '/api/');
const apiFiles = [...api.md.matchAll(/^\| \[`([^`]+)`\]\(([^)]+)\) \| ([^|]+) \|/gm)].map(m => `- [${m[1]}](${m[2]}): ${m[3].trim()}`);
const one = path => en.find(p => p.path === path);

const llms = `# BCI Report

> Public EEG decoding results, each reported with the protocol that produced it: cohort, electrode count, evaluation split, chance level, interval and known limits. A personal, noncommercial research preview; aggregate results only, never raw EEG or per-person scores.

There is no overall ranking: a figure is comparable only with others under the same protocol. Every page states its cohort size and caveats next to the number, and every number is copied from a reviewed download listed below. Each link here is a Markdown copy; drop \`index.md\` for the HTML page. Chinese versions of every page except /data-use/ live under ${origin}/zh/.

## Questions

${topics.map(p => line(p, p.answerText || p.description)).join('\n')}

## Datasets

${[one('/datasets/'), ...by('/datasets/')].map(p => line(p, p.description)).join('\n')}

## Methods

${[one('/methods/'), ...by('/methods/')].map(p => line(p, p.description)).join('\n')}

## Data

${line(api, api.description)}
${apiFiles.join('\n')}

## Optional

${line(home, home.description)}
${line(one('/releases/'), one('/releases/').description)}
${line(one('/data-use/'), one('/data-use/').description)}
`;
writeFileSync(join(dist, 'llms.txt'), llms);

// --- llms-full.txt: every English page in one file ------------------------------------------
const full = [home, ...topics, one('/datasets/'), ...by('/datasets/'), one('/methods/'), ...by('/methods/'), api, one('/releases/'), one('/data-use/')]
  .map(p => p.md.trim()).join('\n\n');
writeFileSync(join(dist, 'llms-full.txt'), `# BCI Report — full text\n\n> Every English page of ${origin} as Markdown, in the order of ${origin}/llms.txt.\n\n${full}\n`);

console.log(`agent files: ${pages.length} Markdown copies, llms.txt (${llms.length} bytes), llms-full.txt; in ${relative(process.cwd(), dist) || '.'}`);
