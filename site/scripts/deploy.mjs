// Deploy dist/ to Cloudflare, confirm production serves the new bytes, then
// tell IndexNow which pages changed.
//
//   npm run deploy                 deploy, verify, ping
//   npm run deploy -- --no-ping    deploy and verify only
//   npm run deploy -- --dry-run    show what would be pinged; deploy nothing
//   npm run deploy -- --no-deploy  verify production and ping, for a deploy already made
//
// Why each step is here:
//
// Wrangler sometimes prints its success line ("Current Version ID") and then
// never exits (2026-09-27, twice). Piping it through `tail` made a finished
// deploy look hung. This script watches for the success line and ends the
// process itself.
//
// IndexNow (https://www.indexnow.org/documentation) shares one submission with
// Bing, Yandex, Seznam, Naver, Yep and others; Bing's index is what ChatGPT
// search and Copilot read from. The protocol asks for URLs that were added,
// updated or deleted — not the whole site on every deploy — so the script keeps
// a fingerprint of each sitemap page as it was last submitted
// (.indexnow-state.json, local and git-ignored) and submits only the
// difference. Fingerprints ignore the hashed /_astro/ asset names, so a CSS-only
// change does not resubmit every page. The first run submits everything.
//
// The key is public by design: IndexNow verifies ownership by fetching
// https://<host>/<key>.txt, which public/ ships.
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { existsSync, readFileSync, readdirSync, writeFileSync, createWriteStream } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const root = fileURLToPath(new URL('..', import.meta.url));
const dist = join(root, 'dist');
const statePath = join(root, '.indexnow-state.json');
const args = new Set(process.argv.slice(2));
const dryRun = args.has('--dry-run');
const noPing = args.has('--no-ping');
const noDeploy = args.has('--no-deploy');

const die = msg => { console.error(`deploy: ${msg}`); process.exit(1); };

// --- What is about to ship ---------------------------------------------------
if (!existsSync(join(dist, 'sitemap.xml'))) die('dist/ has no sitemap.xml — run `npm run build` first.');
const keyFile = readdirSync(join(root, 'public')).find(f => /^[0-9a-f]{32}\.txt$/.test(f));
if (!keyFile) die('no IndexNow key file (public/<32 hex>.txt).');
const key = keyFile.slice(0, -4);
if (readFileSync(join(root, 'public', keyFile), 'utf8').trim() !== key) die(`${keyFile} must contain exactly its own name.`);
if (!existsSync(join(dist, keyFile))) die(`${keyFile} is missing from dist/ — rebuild.`);

const sitemap = readFileSync(join(dist, 'sitemap.xml'), 'utf8');
const urls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
const origin = new URL(urls[0]).origin;
const fileOf = url => {
  const path = decodeURIComponent(new URL(url).pathname);
  return join(dist, path.endsWith('/') ? `${path}index.html` : path);
};
const normalise = html => html.replace(/\/_astro\/[^"')\s]+/g, '/_astro/*');
const fingerprint = bytes => createHash('sha256').update(normalise(bytes.toString('utf8'))).digest('hex');
const current = Object.fromEntries(urls.map(u => [u, fingerprint(readFileSync(fileOf(u)))]));

let previous = {};
try { previous = JSON.parse(readFileSync(statePath, 'utf8')).pages ?? {}; } catch { /* first run */ }
const changed = urls.filter(u => previous[u] !== current[u]);
const removed = Object.keys(previous).filter(u => !(u in current));
const toSubmit = [...changed, ...removed];

console.log(`deploy: ${urls.length} pages in the sitemap; ${changed.length} new or changed, ${removed.length} removed since the last submission.`);
if (dryRun) {
  for (const u of toSubmit) console.log(`  would submit ${u}`);
  process.exit(0);
}

// --- Deploy --------------------------------------------------------------------
const logPath = join(root, '.deploy.log');
if (!noDeploy) await new Promise((resolve, reject) => {
  const log = createWriteStream(logPath);
  const child = spawn('npx', ['wrangler', 'deploy'], {
    cwd: root, env: { ...process.env, WRANGLER_SEND_METRICS: 'false' }, stdio: ['ignore', 'pipe', 'pipe'],
  });
  let done = false, output = '';
  const onData = chunk => {
    const text = chunk.toString();
    output += text; log.write(text); process.stdout.write(text);
    if (!done && /Current Version ID/.test(output)) {
      done = true;
      // Give wrangler a moment to exit on its own, then end it.
      setTimeout(() => { if (child.exitCode === null) child.kill('SIGTERM'); resolve(); }, 5000);
    }
  };
  child.stdout.on('data', onData);
  child.stderr.on('data', onData);
  child.on('exit', code => {
    log.end();
    if (done) resolve();
    else reject(new Error(`wrangler exited with ${code} before reporting a version (log: ${logPath})`));
  });
}).catch(e => die(e.message));

// --- Verify production serves these bytes ------------------------------------------
// The edge can briefly serve the previous copy, so retry before calling it a mismatch.
// Ask for gzip or brotli: the edge otherwise answers zstd, which Node's fetch
// hands back still compressed, and every page would look different.
const get = u => fetch(u, { headers: { 'cache-control': 'no-cache', 'accept-encoding': 'gzip, br' } });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const mismatched = [];
for (const u of changed.length ? changed : urls.slice(0, 3)) {
  const want = readFileSync(fileOf(u));
  let ok = false;
  for (let attempt = 0; attempt < 6 && !ok; attempt++) {
    if (attempt) await sleep(3000);
    const res = await get(u).catch(() => null);
    ok = !!res && res.ok && Buffer.from(await res.arrayBuffer()).equals(want);
  }
  if (!ok) mismatched.push(u);
}
const keyRes = await get(`${origin}/${keyFile}`).catch(() => null);
const keyLive = !!keyRes && keyRes.ok && (await keyRes.text()).trim() === key;
if (mismatched.length) die(`production does not match dist/ for:\n  ${mismatched.join('\n  ')}\nNothing was submitted to IndexNow.`);
console.log(`deploy: production matches dist/ for ${changed.length || 3} checked page(s).`);

// --- IndexNow ----------------------------------------------------------------------
if (noPing) { console.log('deploy: --no-ping, IndexNow skipped.'); process.exit(0); }
if (!keyLive) die(`${origin}/${keyFile} is not serving the key; IndexNow would reject the submission.`);
if (!toSubmit.length) { console.log('deploy: no page changed; nothing to submit to IndexNow.'); process.exit(0); }

const body = { host: new URL(origin).host, key, keyLocation: `${origin}/${keyFile}`, urlList: toSubmit };
const res = await fetch('https://api.indexnow.org/indexnow', {
  method: 'POST', headers: { 'content-type': 'application/json; charset=utf-8' }, body: JSON.stringify(body),
}).catch(e => die(`IndexNow request failed: ${e.message}`));
const meaning = {
  200: 'accepted', 202: 'received; key validation pending', 400: 'invalid format',
  403: 'key not valid', 422: 'URLs do not belong to the host, or the key does not match',
  429: 'too many requests',
}[res.status] ?? 'unexpected response';
console.log(`deploy: IndexNow ${res.status} (${meaning}) for ${toSubmit.length} URL(s).`);
if (res.status === 200 || res.status === 202) {
  writeFileSync(statePath, JSON.stringify({ submittedAt: new Date().toISOString(), pages: current }, null, 2) + '\n');
} else {
  die(`IndexNow did not accept the submission; state left unchanged so the next deploy retries.${res.headers.get('retry-after') ? ` Retry-After: ${res.headers.get('retry-after')}` : ''}`);
}
