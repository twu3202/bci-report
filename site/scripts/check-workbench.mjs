// Application-state tests with minimal DOM doubles; this is not browser or WebMCP integration QA.
import assert from 'node:assert/strict';
import {existsSync,readFileSync,readdirSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import vm from 'node:vm';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
// foundation-models-zh.ts enDisplay: a released sentence that names an internal evaluation version
// prints without it (no version labels on the site, owner 2026-10-08); the JSON keeps it as released.
const EN_SHOWN={'not run by design: LUNA Large is frozen probes only in the v9 stage specification':'not run by design: LUNA Large is frozen probes only in this evaluation\u2019s specification'};
// The built site under test. SITE_DIST points the checks at another build
// (e.g. `astro build --outDir <dir>`) without touching dist/.
const DIST=process.env.SITE_DIST?pathToFileURL(resolve(process.env.SITE_DIST)+'/').href:new URL('../dist/',import.meta.url).href;
const data=JSON.parse(readFileSync(new URL('../src/data/mvp.json',import.meta.url),'utf8'));
const topics=JSON.parse(readFileSync(new URL('../src/data/deployment-topics.json',import.meta.url),'utf8'));
class Element {
  constructor(){this.value='';this.innerHTML='';this.textContent='';this.dataset={};this.events={};this.attributes={};this.open=false;this.scrollWidth=0;this.clientWidth=0;}
  addEventListener(name,fn){this.events[name]=fn;}
  setAttribute(k,v){this.attributes[k]=v;}
  removeAttribute(k){delete this.attributes[k];}
  focus(){}
  showModal(){this.open=true;}
  close(){this.open=false;}
}
const elements=new Map();
const get=s=>{if(!elements.has(s))elements.set(s,new Element());return elements.get(s);};
get('#family-filter').value='all';get('#sort-results').value='name';
// The v9 rows (2026-10-04) reach workbench.ts as JSON the home page embeds (#fm-rows), in the
// page's language. The DOM double gets the same JSON, read from the built page; the v9 pages
// block below holds that JSON to the served per-protocol CSVs.
const fmEmbedded=lang=>{const html=readFileSync(new URL((lang==='zh'?'zh/':'')+'index.html',DIST),'utf8');
  const m=html.match(/<script type="application\/json" id="fm-rows">([\s\S]*?)<\/script>/);
  assert.ok(m,'run `npm run build` first: the home page must embed the v9 rows as JSON (#fm-rows)');return m[1];};
const fmHome=JSON.parse(fmEmbedded('en'));
const fmMatrixOf=id=>fmHome.tracks[id].rows.filter(r=>r.panel==='matrix');
get('#fm-rows').textContent=fmEmbedded('en');
const registered=[];
const document={querySelector:get,querySelectorAll:()=>[],modelContext:{registerTool:t=>registered.push(t)}};
const source=readFileSync(new URL('../src/scripts/workbench.ts',import.meta.url),'utf8').replace(/^import data[^\n]+\n/,'');
vm.runInNewContext(stripTypeScriptTypes(source),{data,document,window:{addEventListener(){}},AbortController,Promise,console});
assert.match(get('#result-rows').innerHTML,/LaBraM/);
assert.match(get('#result-chart').innerHTML,/<svg/);
assert.equal(registered.length,1);
const tool=registered[0];
assert.equal(tool.name,'configure_eeg_comparison');
assert.equal(tool.annotations.readOnlyHint,false);
for(const t of data.tracks){
  const output=tool.execute({trackId:t.id,family:'all'});
  // The released rows, then the v9 matrix rows (2026-10-04), each named with its release.
  assert.equal(output.models.length,t.rows.length+fmMatrixOf(t.id).length);
  assert.ok(output.models.slice(t.rows.length).every(m=>m.release==='foundation-models-update-20261004'),t.id+': the tool names the v9 rows\' release');
  assert.equal(get('#download-results').href,'/data/'+t.id+'-results.csv');
  assert.equal(get('#track-tabs').attributes['data-active'],t.id);
  assert.equal(get('#track-panel').attributes['aria-labelledby'],'tab-'+t.id);
  assert.equal(get('#track-title').textContent,t.subtitle);
}
assert.throws(()=>tool.execute({trackId:'transfer',family:'all'}),/Invalid/,'removed tracks must not resolve');
// Every track currently has a model in every family, so the empty state is not
// reachable through the tool's validated enum; drive the filter directly so the
// branch stays covered.
get('#family-filter').value='__no_such_family__';get('#family-filter').events.change();
assert.match(get('#result-rows').innerHTML,/No evaluated models/);
assert.match(get('#result-chart').innerHTML,/No results/);
get('#family-filter').value='all';get('#family-filter').events.change();
const state=get('#track-title').textContent;
assert.throws(()=>tool.execute({trackId:'bogus'}),/Invalid/);
assert.throws(()=>tool.execute({trackId:'idle',family:'anything'}),/Invalid/);
assert.throws(()=>tool.execute({trackId:'idle',extra:true}),/Invalid/);
assert.equal(get('#track-title').textContent,state);
tool.execute({trackId:'idle',family:'all'});
get('#sort-results').value='y-desc';get('#sort-results').events.change();
assert.ok(get('#result-rows').innerHTML.indexOf('ShallowFBCSPNet')<get('#result-rows').innerHTML.indexOf('EEGNet'));
// A coverage-matrix column heading must drive the protocol panel below it.
get('#overview').events.click({target:{closest:()=>({dataset:{jump:'sleep-scalp'}})}});
assert.equal(get('#track-tabs').attributes['data-active'],'sleep-scalp');
assert.equal(get('#track-title').textContent,data.tracks.find(t=>t.id==='sleep-scalp').subtitle);
get('#overview').events.click({target:{closest:()=>null}});
assert.equal(get('#track-tabs').attributes['data-active'],'sleep-scalp','a click on matrix whitespace must change nothing');
tool.execute({trackId:'idle',family:'all'});
get('#open-protocol').events.click();assert.equal(get('#detail-dialog').open,true);
assert.match(get('#dialog-body').innerHTML,/calibration/);
get('#close-dialog').events.click();assert.equal(get('#detail-dialog').open,false);
get('#result-rows').events.click({target:{closest:()=>({dataset:{model:'cbramod'}})}});
assert.match(get('#dialog-body').innerHTML,/17 ch · 4 participants/);
assert.match(get('#dialog-body').innerHTML,/always-abstain/);
assert.equal(get('#detail-dialog').open,true);
assert.equal(/\p{Script=Han}/u.test(JSON.stringify(data)),false);
for(const t of data.tracks){
  const csv=readFileSync(new URL('../public/data/'+t.id+'-results.csv',import.meta.url),'utf8');
  assert.equal(csv.trim().split(/\r?\n/).length,t.rows.length+1);
  assert.equal(new Set(t.rows.map(r=>r.id)).size,t.rows.length);
  assert.ok(t.rows.every(r=>r.y>=0&&r.y<=100&&r.seconds>=0));
}
assert.ok(data.news.every(n=>/^https:\/\//.test(n.sourceUrl)));

// Caveats must travel with the number, not only live in a dialog.
for(const t of data.tracks){
  tool.execute({trackId:t.id,family:'all'});
  const html=get('#result-rows').innerHTML;
  const seed=t.seedSensitivity;
  if(seed){
    const v=seed.balancedAccuracyPercent,hi=Math.max(...v),lo=Math.min(...v);
    const word=v[0]>=hi?'highest':v[0]<=lo?'lowest':'middle';
    assert.match(html,new RegExp('the '+word+' of '+v.length+' run'),t.id+': seed rank must be stated in the table');
  }
  for(const r of t.rows){
    if(t.type==='tradeoff'&&r.abstain)
      assert.match(html,new RegExp(r.abstain+' of '+r.subjects+' participants always abstained'),t.id+'/'+r.id+': abstain count must be in the table');
    if(t.chanceLevel!=null&&t.type!=='tradeoff'){
      if(r.y<=t.chanceLevel) assert.match(html,/At or below the /,t.id+'/'+r.id+': at-or-below-chance must be flagged');
      else if(r.interval&&r.interval[0]<=t.chanceLevel) assert.match(html,/Interval reaches the /,t.id+'/'+r.id+': chance-touching interval must be flagged');
    }
  }
  if(t.chanceLevel!=null&&t.type!=='tradeoff'){
    assert.match(get('#result-chart').innerHTML,/stroke-dasharray/,t.id+': chart needs a chance reference line');
    assert.match(get('#chart-note').textContent,new RegExp(t.chanceLevel+'% chance level'),t.id+': note must name the chance level');
  }
}

// The licence is a sentence on some tracks (semantic-target: 75 characters). In
// a no-wrap button it ran ~180px past a phone-width dialog; the button now says
// "Licence" and the sentence is printed as text.
tool.execute({trackId:'semantic-target',family:'all'});
get('#open-protocol').events.click();
{
  const t=data.tracks.find(t=>t.id==='semantic-target');
  assert.ok(get('#dialog-body').innerHTML.includes('<span>'+t.license+'</span>'),'protocol dialog prints the licence as text');
  for(const [,label] of get('#dialog-body').innerHTML.matchAll(/<a class="button"[^>]*>([^<]*)<\/a>/g))
    assert.ok(label.length<=30,'a dialog button label must stay short enough for a phone: "'+label+'"');
  assert.match(get('#chart-legend').innerHTML,/^<li><i class="s0"><\/i><span class="n">1<\/span>/,'the chart legend is numbered, matching the 1..n axis');
}
get('#close-dialog').events.click();
// The seed-sensitivity scope sentence exists in the data; it must be rendered.
tool.execute({trackId:'mi-rest',family:'all'});
get('#open-protocol').events.click();
assert.match(get('#dialog-body').innerHTML,/no best-seed selection/,'protocol dialog must render seedSensitivity.scope');
assert.match(get('#dialog-body').innerHTML,/retained seed is also the highest/,'protocol dialog must state where the retained seed sits');
get('#close-dialog').events.click();
// A JSON fragment in the release text ('… · {"mirror": …, "upstream": …}') prints as its fields, as on the protocol pages.
for(const t of data.tracks.filter(t=>/\{[^{}]*\}/.test(t.version))){
  tool.execute({trackId:t.id,family:'all'});get('#open-protocol').events.click();
  const frag=t.version.match(/\{[^{}]*\}/)[0],printed=t.version.replace(frag,Object.entries(JSON.parse(frag)).map(([k,v])=>k+' '+v).join(' · '));
  assert.ok(get('#dialog-body').innerHTML.includes('<span>'+printed+'</span>'),t.id+': the dialog prints the release version\'s fields');
  assert.doesNotMatch(get('#dialog-body').innerHTML,/\{&quot;/,t.id+': no JSON fragment printed raw in the dialog');
  get('#close-dialog').events.click();
}
// The privacy review reads as the reviewer's working notes. Since the 2026-10-02 review the
// dialog treats it as the protocol pages do: the site sentence, any consent caveat, the public-data
// register's reviewed rights note for the dataset, and a link to the protocol JSON that holds the
// full note. That the sentence and caveat are the pages' own is checked with the protocol pages.
const escHtml=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
for(const t of data.tracks){
  tool.execute({trackId:t.id,family:'all'});get('#open-protocol').events.click();
  const body=get('#dialog-body').innerHTML;
  assert.ok(!body.includes(escHtml(t.privacyReview))&&!body.includes(escHtml(t.privacyReview.slice(0,80))),t.id+': the dialog no longer prints the privacy review verbatim');
  const pv=body.indexOf('<p class="protocol-privacy">'),privacy=pv<0?'':body.slice(pv,body.indexOf('</p>',pv));
  assert.ok(privacy.startsWith('<p class="protocol-privacy"><strong>Privacy</strong> Only cohort aggregates are published here: no recording, no participant identifier, no per-person score.'),t.id+': the dialog\'s privacy sentence');
  assert.ok(privacy.endsWith(` <a href="/data/${t.id}-protocol.json" download>The full review note is in the protocol JSON ↓</a>`),t.id+': the privacy sentence links the protocol JSON');
  assert.equal(/Region Midt/.test(privacy),t.id==='sleep-scalp',t.id+': the consent caveat is the sleep protocol\'s');
  const detail=data.datasets.find(d=>d.name===t.dataset)?.detail;
  assert.ok(detail&&body.includes('<p class="protocol-register"><strong>Public-data register note</strong> <span>'+escHtml(detail)+'</span></p>'),t.id+': the register\'s reviewed rights note for '+t.dataset);
  assert.ok(body.indexOf('class="protocol-register"')>pv,t.id+': the register note follows the privacy sentence');
  get('#close-dialog').events.click();
}
// The same script on the Chinese page. render() replaces the server markup, and
// it used to drop every lang="en" the server had set, so a screen reader read
// the English payload in a Chinese voice after the first paint.
{
  const els=new Map(),zget=s=>{if(!els.has(s))els.set(s,new Element());return els.get(s);};
  zget('#family-filter').value='all';zget('#sort-results').value='name';
  const zdoc={querySelector:zget,querySelectorAll:()=>[],documentElement:{lang:'zh-Hans'}};
  vm.runInNewContext(stripTypeScriptTypes(source),{data,document:zdoc,window:{addEventListener(){}},AbortController,Promise,console});
  const t0=data.tracks[0];
  assert.equal((zget('#result-rows').innerHTML.match(/<small lang="en">/g)||[]).length,t0.rows.length*3,'zh: mode, primary and secondary details keep lang="en" after the client re-render');
  assert.match(zget('#track-meta').innerHTML,/<span lang="en">[^<]+<\/span>$/,'zh: observations and exposure keep lang="en"');
  assert.match(zget('#track-rights').innerHTML,/^<span lang="en">[^<]+<\/span> · 聚合研究结果$/,'zh: the licence keeps lang="en"');
  zget('#open-protocol').events.click();
  const proto=zget('#dialog-body').innerHTML;
  assert.match(proto,/^<p lang="en">[^<]+<\/p><ol lang="en">/,'zh: the protocol subtitle and steps are marked English');
  assert.match(proto,/<p>许可：<span lang="en">/,'zh: the licence is printed, marked English');
  assert.match(proto,/>许可 ↗<\/a>$/,'zh: the licence button has a short Chinese label');
  // The privacy treatment, in Chinese; the register note stays English, marked so (the script does not read directory-zh.json).
  for(const t of data.tracks){
    zget('#track-tabs').events.click({target:{closest:()=>({dataset:{track:t.id}})}});zget('#open-protocol').events.click();
    const body=zget('#dialog-body').innerHTML,pv=body.indexOf('<p class="protocol-privacy">'),privacy=pv<0?'':body.slice(pv,body.indexOf('</p>',pv));
    assert.ok(privacy.startsWith('<p class="protocol-privacy"><strong>隐私</strong> 这里只发布队列级聚合结果：不发布任何记录、被试编号或逐人分数。'),'zh/'+t.id+': the dialog\'s privacy sentence');
    assert.ok(privacy.endsWith(` <a href="/data/${t.id}-protocol.json" download>完整的审查说明在协议 JSON 中 ↓</a>`),'zh/'+t.id+': the privacy sentence links the protocol JSON');
    assert.equal(/Region Midt/.test(privacy),t.id==='sleep-scalp','zh/'+t.id+': the consent caveat is the sleep protocol\'s');
    assert.ok(!body.includes(escHtml(t.privacyReview.slice(0,80))),'zh/'+t.id+': no privacy review verbatim');
    assert.ok(body.includes('<p class="protocol-register"><strong>公开数据登记说明</strong> <span lang="en">'+escHtml(data.datasets.find(d=>d.name===t.dataset).detail)+'</span></p>'),'zh/'+t.id+': the register note, marked English');
  }
  zget('#result-rows').events.click({target:{closest:()=>({dataset:{model:t0.rows[0].id}})}});
  assert.match(zget('#dialog-body').innerHTML,/^<p><span lang="en">[^<]+<\/span> · \d+ ch · /,'zh: the model dialog marks the training mode English');
  assert.equal((zget('#dialog-body').innerHTML.match(/<small lang="en">/g)||[]).length,2,'zh: both metric details in the model dialog are marked English');
}
// --- Coverage matrix -------------------------------------------------------
// It is server-rendered, so the client script above never touches it and none
// of the assertions so far cover it — yet it is now the first thing a visitor
// reads. Check it against the data rather than trusting the template.
const builtPath=new URL(DIST+'index.html',import.meta.url);
assert.ok(existsSync(builtPath),'run `npm run build` first: the coverage matrix is checked against dist/index.html');
const built=readFileSync(builtPath,'utf8');
const attr=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const count=re=>(built.match(re)||[]).length;
let cells=0,below=0;
const named=new Set();
for(const t of data.tracks) for(const r of t.rows){
  cells++;named.add(r.name);
  assert.ok(built.includes(attr(r.name+' · '+t.title+': '+r.y.toFixed(1)+'% '+t.yLabel.toLowerCase())),
    'matrix is missing '+r.name+' on '+t.id);
  // The bar is normalised against this protocol's OWN chance level. A global
  // normalisation would invite exactly the cross-task reading the page denies.
  // Round the raw value exactly as index.astro does. Rounding a value that has
  // already been fixed to one decimal disagrees with it on .x5 boundaries —
  // beta-4ch/cca is 56.4927, which toFixed(1) lifts to 56.5 and Math.round
  // then takes to 57.
  const c=t.chanceLevel ?? 0,w=Math.round(Math.max(0,Math.min(100,(r.y-c)/(100-c)*100)));
  assert.ok(built.includes('class="bar w'+w+'"></span></span><span class="num">'+r.y.toFixed(1)+'</span>'),
    t.id+'/'+r.id+': bar length must be chance-relative and tied to its own number');
  if(t.chanceLevel!=null&&r.y<=t.chanceLevel)below++;
}
assert.equal(cells,data.coverage.displayedComparisons,'matrix must show every displayed comparison');
assert.equal(count(/class="cell none"/g),named.size*data.tracks.length-cells,'blank cells must be methods x protocols minus comparisons');
assert.equal(count(/data-rank="sub"/g),below,'every at-or-below-chance cell must be marked');
assert.equal(count(/data-rank="lead"/g),data.tracks.filter(t=>t.type!=='tradeoff').length,'exactly one leader per accuracy protocol');
for(const tag of built.match(/<td class="cell"[^>]*>/g)||[])
  if(tag.includes('data-rank="lead"'))
    assert.ok(!tag.includes('Idle &amp; command'),'detection alone must not crown a leader on the tradeoff protocol');
assert.match(built,/comparable <strong>down<\/strong> a column and not <strong>across<\/strong>/,'the matrix must say bars do not compare sideways');
// These pinned the count "82". The topics now draw on two exports measuring
// different things (proportions, correlation, R²), so a summed total would be
// the inflation these checks exist to prevent. The intent is kept, not the number.
assert.match(built,/separate from the questions below/,'homepage must distinguish the topic extension from the 39-comparison matrix');
assert.match(built,/not independent experiments, and not an overall ranking/,'homepage must not inflate repeated conditions into independent experiments');
assert.doesNotMatch(built,/\d+ additional aggregate measurements/,'no summed measurement count across exports that measure different things');
// Every protocol is reachable without JavaScript and without a dropdown. Since
// 2026-10-02 the column heading is a real link to the protocol's own page.
for(const t of data.tracks){
  assert.ok(built.includes('data-jump="'+t.id+'"'),t.id+': needs a matrix column heading');
  assert.ok(built.includes('href="/protocols/'+t.id+'/" data-jump="'+t.id+'"'),t.id+': the matrix column heading must link to its protocol page');
  assert.ok(built.includes('data-track="'+t.id+'"'),t.id+': needs a protocol tab');
}
assert.equal(count(/class="track-tab"/g),data.tracks.length);
// The small-cohort caveat is a claim about what the published numbers allow,
// not decoration: on the four-person idle track the mean is invertible to a
// count. Pinned so a copy edit cannot quietly drop it.
const policy=readFileSync(new URL(DIST+'data-use/index.html',import.meta.url),'utf8');
assert.match(policy,/id="small-cohorts"/,'the data-use page must keep the small-cohort caveat');
// The CSP in public/_headers allows no inline style and no inline script. An
// inline style attribute here does not throw — it is silently dropped by the
// browser, which is how every matrix bar reached production empty.
// [slug, h1]. The h1 is the page's question, as a reader would ask it; the
// short label stays in the breadcrumb and on the cards (src/data/i18n.ts).
const topicPages=[
  ['dry-vs-wet','Do dry EEG electrodes decode as well as wet ones?'],
  ['screen-to-vr','Does a P300 decoder calibrated on a screen still work in VR?'],
  ['fewer-electrodes','Can fewer electrodes, or electrodes in the ear, match a full scalp montage?'],
  ['clinical-groups','Can resting-state EEG separate Parkinson&#39;s disease from controls?'],
  ['on-the-move','Does EEG decoding still work while walking or running?'],
  // Broadened on 2026-10-03 (owner decision): the OpenBMI next session sits beside the wearable SSVEP result.
  ['calibration-budget','How much calibration data does an EEG decoder need?'],
  // Split from calibration-budget on 2026-10-02 (owner approved): new people and the next day.
  ['model-adaptation','New people, next day: which part of a pretrained model should you update?'],
  ['when-not-to-act','How often does an EEG decoder fire when nobody is giving a command?'],
  // Since 2026-10-03 (owner decision): Dreem sleep staging, two cohorts kept apart.
  ['sleep-staging','Why can a sleep stager be right most of the time and still miss whole stages?'],
  ['does-pretraining-help','Does pretraining help EEG foundation models like LaBraM and CBraMod?'],
  // Since 2026-10-07 (owner approval): route 2 of the decision-research plan, one model for several questions.
  ['shared-encoder','Can one EEG model answer several questions about the same data as well as separate models, and at what cost?'],
  // Owner decision: the large-source batch's later-session results (WBCIC-SHU, longitudinal RSVP, Forenzo).
  ['later-sessions','Does a decoder trained on an earlier session still work later?'],
];
const dataFileOf=slug=>slug==='fewer-electrodes'?'evidence-update.json'
  :slug==='model-adaptation'?'adaptation-update.json'
  :slug==='clinical-groups'?'clinical-update.json'
  :slug==='when-not-to-act'?'experiments.json'
  :slug==='screen-to-vr'?'context-update.json'
  :slug==='sleep-staging'?'large-source-update.json'
  :slug==='shared-encoder'?'shared-representation-update.json'
  :slug==='later-sessions'?'later-sessions-update.json':'deployment-topics.json';
for(const [slug,title] of topicPages){
  const page=DIST+'topics/'+slug+'/index.html';
  const html=readFileSync(new URL(page,import.meta.url),'utf8');
  assert.ok(html.includes('<h1>'+title+'</h1>'),slug+': page title must render in the initial HTML');
  assert.ok(html.includes('href="/data/'+dataFileOf(slug)+'"'),slug+': the reviewed export holding its figures must be reachable');
  assert.ok(html.includes('aria-label="Breadcrumb"'),slug+': breadcrumb is required');
  assert.ok(html.includes('rel="canonical"'),slug+': canonical link is required');
}
const sitemap=readFileSync(new URL(DIST+'sitemap.xml',import.meta.url),'utf8');
// The later-sessions export, as served (its own block near the end reads it in full).
const LTX=JSON.parse(readFileSync(new URL('data/later-sessions-update.json',DIST),'utf8'));
for(const [slug] of topicPages)
  assert.ok(sitemap.includes('https://bci.report/topics/'+slug+'/'),slug+': sitemap entry is required');
const motionPage=readFileSync(new URL(DIST+'topics/on-the-move/index.html',import.meta.url),'utf8');
assert.match(motionPage,/−0\.276 AUC/,'ERP motion change must use signed native AUC units');
assert.match(motionPage,/−0\.322 to −0\.227 AUC/,'ERP motion interval must use native AUC units');
assert.match(motionPage,/Bars span 0–100%; chance is 33\.3%/,'SSVEP bars must state their full scale and chance level');
assert.match(motionPage,/10\.82901\/nemar\.nm000125/,'mobile SSVEP credit must include its dataset DOI');
assert.match(motionPage,/10\.82901\/nemar\.nm000201/,'mobile ERP credit must include its dataset DOI');
assert.match(motionPage,/10\.1038\/s41597-021-01094-4/,'mobile pages must credit the source study DOI');
const sensorPage=readFileSync(new URL(DIST+'topics/dry-vs-wet/index.html',import.meta.url),'utf8');
assert.match(sensorPage,/10\.6084\/m9\.figshare\.13560281\.v4/,'wearable credit must include the versioned dataset DOI');
assert.match(sensorPage,/10\.3390\/s21041256/,'wearable credit must include the Sensors paper DOI');
const pretrainingPage=readFileSync(new URL(DIST+'topics/does-pretraining-help/index.html',import.meta.url),'utf8');
assert.match(pretrainingPage,/href="\/data-use\/#sources"/,'seed sensitivity table must link to its dataset citations');
for(const page of [DIST+'index.html',DIST+'data-use/index.html',DIST+'404.html',...topicPages.map(([slug])=>DIST+'topics/'+slug+'/index.html')]){
  const html=readFileSync(new URL(page,import.meta.url),'utf8');
  assert.doesNotMatch(html,/\sstyle="/,page+': the CSP forbids style attributes');
  assert.doesNotMatch(html,/<style[\s>]/,page+': the CSP forbids inline <style> blocks');
  assert.doesNotMatch(html,/\son(?:click|load|error|change|submit)=/,page+': the CSP forbids inline handlers');
}
// The built bundle, not the source: comments are stripped there, so this tests
// what actually ships rather than what the file happens to say about itself.
for(const js of readdirSync(new URL(DIST+'_astro/',import.meta.url)).filter(f=>f.endsWith('.js')))
  assert.doesNotMatch(readFileSync(new URL(DIST+'_astro/'+js,import.meta.url),'utf8'),
    /style="|\.style\.|setAttribute\(['"`]style/,js+': the client script must not inject inline style either');
// The masthead is styled through .site-header. A bare `header{` rule made the
// date row of every release entry a second sticky bar painted over the site
// navigation; a bare `nav{` laid the topic switcher out sideways.
for(const css of readdirSync(new URL(DIST+'_astro/',import.meta.url)).filter(f=>f.endsWith('.css')))
  assert.doesNotMatch(readFileSync(new URL(DIST+'_astro/'+css,import.meta.url),'utf8'),/(?:^|[{},])\s*(?:header|nav)\s*\{/,
    css+': a bare header or nav rule styles every <header> and <nav>, not only the masthead');
// The English under a translated licence note in the register's status column, right-aligned on
// wide screens: the margin rule that marks it elsewhere stood away from its text there (2026-10-02).
assert.ok(readdirSync(new URL(DIST+'_astro/',import.meta.url)).filter(f=>f.endsWith('.css')).some(css=>
  /\.dataset-status \.note-original\{border-left:0;padding-left:0\}/.test(readFileSync(new URL(DIST+'_astro/'+css,import.meta.url),'utf8'))),
  'the status column drops the original-text margin rule');
// The home table's v9 rows (review of 2026-10-05): the table is nowrap, and ZUNA 1.1's research-use line and the long
// checkpoint names and modes inherited it, widening the first column until no score fitted a 375 px screen and the
// table overflowed at 1280 px. The DOM doubles cannot measure layout, so the wrapping rules are pinned in what ships.
{
  const css=readdirSync(new URL(DIST+'_astro/',import.meta.url)).filter(f=>f.endsWith('.css')).map(f=>readFileSync(new URL(DIST+'_astro/'+f,import.meta.url),'utf8')).join('\n');
  const rule=css.match(/(?:^|})([^{}]*\.fm-row \.model-name[^{}]*)\{([^}]*)\}/);
  assert.ok(rule&&/white-space:normal/.test(rule[2])&&['.fm-research-use','.fm-row .model-name','.fm-row td:first-child small'].every(s=>rule[1].split(',').map(x=>x.trim()).includes(s)),
    'the v9 rows\' names, modes and research-use line wrap in the home table');
  assert.match(css,/\.fm-row \.model-name\{text-align:left\}/,'a wrapped v9 name stays left-aligned');
  // Follow-up review of 2026-10-05: the v9 group's heading spans the whole table, which scrolls sideways on a phone, so
  // at 375 px it was cut after "13 further foundation encoders". Its words wrap within the visible box and stay there.
  const g=css.match(/(?:^|})([^{}]*\.fm-group-label[^{}]*)\{([^}]*)\}/);
  assert.ok(g&&['white-space:normal','display:block','position:sticky','left:18px'].every(d=>g[2].split(';').includes(d))&&/max-width:calc\(100vw - \d+px\)/.test(g[2]),
    'the v9 group heading wraps within the visible box and stays in view while the rows scroll');
  for(const p of ['','zh/']) assert.match(readFileSync(new URL(p+'index.html',DIST),'utf8'),/<tr class="fm-group"><th colspan="4" scope="colgroup"><span class="fm-group-label">/,p+'index.html: the v9 group heading is held in its label');
}
const headers=readFileSync(new URL('../public/_headers',import.meta.url),'utf8');
assert.match(headers,/Content-Security-Policy:[^\n]*style-src 'self';/,'style-src must stay free of unsafe-inline');
assert.match(headers,/Content-Security-Policy:[^\n]*script-src 'self';/,'script-src must stay free of unsafe-inline');
assert.match(policy,/cannot recover is which person is which/,'it must say what is and is not recoverable');
const idle=data.tracks.find(t=>t.id==='idle');
assert.equal(idle.subjects,4,'the caveat names a cohort of four; update both together if this changes');
assert.ok(idle.rows.some(r=>r.abstain>0),'the caveat relies on abstention counts being published');
assert.equal(count(/aria-selected="true"/g),1,'exactly one protocol tab starts selected');

// --- Reviewed deployment-topic extension ---------------------------------
// The pages must consume the allowlisted aggregate export as-is. This check is
// deliberately structural; publication/privacy gates separately validate that
// the export contains no individual records or private evidence paths.
assert.equal(topics.rows.length,82,'topic export must contain the 82 reviewed aggregate measurements');
assert.equal(topics.paired_contrasts.length,18,'topic export must contain the 18 reviewed paired contrasts');
assert.equal(topics.seed_sensitivity.length,5,'topic export must contain five seed-sensitivity groups');
assert.equal(new Set(topics.rows.map(row=>row.id)).size,topics.rows.length,'topic row ids must be unique');
assert.ok(topics.rows.every(row=>row.value>=0&&row.value<=1),'topic measurements must remain proportions in [0,1]');
assert.ok(topics.rows.every(row=>row.model!=='eegpt'),'EEGPT results are outside the public candidate');
assert.ok(topics.rows.some(row=>row.metric==='participant_mean_roc_auc'),'ERP ROC AUC must stay explicitly typed');
assert.ok(topics.rows.some(row=>row.metric==='participant_mean_balanced_accuracy'),'balanced accuracy must stay explicitly typed');
assert.ok(topics.rows.some(row=>row.track==='mobile-ssvep-2s'&&row.window_seconds===2),'two-second SSVEP protocol is required');
assert.ok(topics.rows.some(row=>row.track==='mobile-ssvep-5s'&&row.window_seconds===5),'five-second SSVEP protocol is required');
assert.ok(topics.rows.some(row=>row.track==='wearable-calibration'&&row.training_regime==='source-only'),'source-only calibration arm is required');
assert.ok(topics.rows.some(row=>row.track==='wearable-calibration'&&row.training_regime==='target-only'),'target-only calibration arm is required');
assert.ok(topics.rows.some(row=>row.track==='pretraining-attribution-fixed'&&row.head_selection==='fixed alpha100'),'fixed readout setting is required');
assert.ok(topics.rows.some(row=>row.track==='pretraining-attribution-selected'&&row.head_selection?.startsWith('inner participant validation')),'train-selected readout setting is required');
assert.deepEqual(
  readFileSync(new URL('../src/data/deployment-topics.json',import.meta.url)),
  readFileSync(new URL('../public/data/deployment-topics.json',import.meta.url)),
  'source and downloadable topic exports must be byte-identical',
);

// --- Chinese pages ------------------------------------------------------------
// The interface and the topic pages exist in Chinese; /data-use/ does not.
// What translation can break without anything visibly failing is pinned here.
const bilingual=['',...topicPages.map(([slug])=>'topics/'+slug+'/')];
const read=p=>readFileSync(new URL(DIST+''+p+'index.html',import.meta.url),'utf8');
const zhTitles={'dry-vs-wet':'干电极的解码效果能和湿电极一样好吗？','fewer-electrodes':'更少的电极、或耳道内电极，能比得上完整的头皮电极吗？','screen-to-vr':'在屏幕上校准的 P300 解码器，换到 VR 里还管用吗？','on-the-move':'走路或跑步时，EEG 解码还管用吗？','clinical-groups':'静息态 EEG 能把帕金森病患者和对照组区分开吗？','calibration-budget':'EEG 解码器需要多少校准数据？','sleep-staging':'为什么睡眠分期器大多数时候判对，却仍会漏掉整类睡眠阶段？','model-adaptation':'新被试、第二天：预训练模型该更新哪一部分？','when-not-to-act':'没有人下指令时，EEG 解码器误触发有多频繁？','does-pretraining-help':'预训练对 LaBraM、CBraMod 这类 EEG 基础模型有帮助吗？','shared-encoder':'一个 EEG 模型回答同一份数据上的多个问题，能和分开的模型一样好吗，代价又是多少？','later-sessions':'在较早会话上训练的解码器，到后来还管用吗？'};
for(const path of bilingual){
  const en=read(path),zh=read('zh/'+path);
  assert.match(en,/<html lang="en"/,path+': English page must declare lang="en"');
  assert.match(zh,/<html lang="zh-Hans"/,'zh/'+path+': Chinese page must declare lang="zh-Hans"');
  // hreflang only counts when it is reciprocal: each version names both, plus x-default.
  for(const [html,name] of [[en,path||'/'],[zh,'zh/'+path]]){
    assert.ok(html.includes(`hreflang="en" href="https://bci.report/${path}"`),name+': must link the English alternate');
    assert.ok(html.includes(`hreflang="zh-Hans" href="https://bci.report/zh/${path}"`),name+': must link the Chinese alternate');
    assert.ok(html.includes(`hreflang="x-default" href="https://bci.report/${path}"`),name+': x-default must be English');
  }
  assert.ok(zh.includes(`rel="canonical" href="https://bci.report/zh/${path}"`),'zh/'+path+': canonical must be self-referencing, not the English page');
  // Translation must not touch a single figure. Every metric cell, in order.
  // Topic pages mark figures `.metric`; the homepage uses `.num` in the matrix
  // and <td><strong> in the results table. Matching only `.metric` compared two
  // empty lists on the homepage and passed without checking anything.
  // `.fig` marks figures in short answers and plot values.
  const figures=html=>[...html.matchAll(/class="(?:metric|num|fig)">([^<]+)<|<td><strong>([^<]+)<\/strong>/g)].map(m=>m[1]??m[2]);
  assert.ok(figures(en).length>0,path+': the figure-parity check found nothing to compare');
  assert.deepEqual(figures(zh),figures(en),'zh/'+path+': every number must equal the English page, in the same order');
  // The data link from a Chinese page leads to an English-only page and says so.
  assert.match(zh,/数据使用[^<]*（英文）/,'zh/'+path+': a link to /data-use/ must be marked as English');
  assert.doesNotMatch(zh,/href="\/zh\/data-use\//,'zh/'+path+': /data-use/ has no Chinese version to link to');
  // One Dataset entity per dataset: structured data lives on the English canonical only.
  assert.doesNotMatch(zh,/application\/ld\+json/,'zh/'+path+': Dataset markup belongs to the English canonical only');
}
for(const [slug] of topicPages){
  const zh=read('zh/topics/'+slug+'/');
  // The h1 carries <wbr> phrase breaks (topicQuestionPhrases in i18n.ts); the
  // words must still be exactly the question.
  const h1=(zh.match(/<h1>([\s\S]*?)<\/h1>/)||[])[1]??'';
  assert.equal(h1.replace(/<wbr>/g,''),zhTitles[slug],slug+': Chinese title must render in the initial HTML');
  assert.ok(h1.includes('<wbr>'),slug+': a Chinese h1 needs phrase breaks, or keep-all lets a phone cut it mid-word');
  assert.ok(zh.includes('href="/data/'+dataFileOf(slug)+'"'),slug+': the same reviewed download, not a translated copy');
}
// Credits survive translation: every DOI on an English topic page is on its Chinese twin.
for(const [slug] of topicPages){
  const dois=html=>new Set([...html.matchAll(/10\.\d{4,9}\/[^\s"<)]+/g)].map(m=>m[0].replace(/[.,;]$/,'')));
  const missing=[...dois(read('topics/'+slug+'/'))].filter(d=>!dois(read('zh/topics/'+slug+'/')).has(d));
  assert.deepEqual(missing,[],slug+': the Chinese page dropped a credit');
}
for(const page of bilingual.map(p=>DIST+'zh/'+p+'index.html')){
  const html=readFileSync(new URL(page,import.meta.url),'utf8');
  assert.doesNotMatch(html,/\sstyle="/,page+': the CSP forbids style attributes');
  assert.doesNotMatch(html,/<style[\s>]/,page+': the CSP forbids inline <style> blocks');
  assert.doesNotMatch(html,/\son(?:click|load|error|change|submit)=/,page+': the CSP forbids inline handlers');
}
// Terminology. One rendering per concept — the glossary is at the top of
// src/data/i18n.ts. Each entry below was on the page once: 被试 appeared as
// three different words on the same homepage, and "12 个标注" on a 12-target
// task read as twelve classes. English elements (lang="en") are excluded.
const rejected={
  '参与者':'被试','受试者':'被试','构造器':'随机初始化','读出头':'分类头','弃权':'拒识',
  '误激活':'误触发','提示门控':'提示同步','心理负荷':'脑力负荷','全距':'极差','区块':'组块',
  '未来组块':'后续组块','有标注':'校准试次','个标注':'个校准试次','谱岭回归':'spectral ridge',
  '解析参考':'免训练参考','暴露':'是否出现在预训练数据中','纠缠':'相互混杂',
  '三种子':'三个随机种子 (三种子 also parses as 三种·子, three kinds)',
  '导 EEG':'通道 EEG (多导睡眠图 stays)','个百分点':'pp, with 百分点 named once on the page','个 epoch':'轮 (训练 5 轮)',
  '冻结的编码器':'冻结编码器','最后一个 block':'最后一个 Transformer 块',
  // Descriptive method labels: modelLabel(model, locale) prints the Chinese.
  'Author-style CCA':'CCA（按原作者设置）','Single-band eTRCA':'单频带 eTRCA','Uniform random':'均匀随机',
};
const chineseOnly=html=>html.replace(/<script[\s\S]*?<\/script>/g,'').replace(/<(\w+)[^>]*\blang="en"[^>]*>[\s\S]*?<\/\1>/g,'');
// 暴露 is rejected for pretraining exposure. Two rights-review notes in the data
// register say 隐私暴露 and 元数据暴露 (privacy and metadata exposure, decided
// 2026-10-02), a different concept the glossary names; those two words, and
// nothing else with 暴露 in it, pass.
const allowedWith={'暴露':/(?:隐私|元数据)暴露/g};
const hasRejected=(text,bad)=>(allowedWith[bad]?text.replace(allowedWith[bad],''):text).includes(bad);
// The release log is checked here too; the API page is checked with the entity pages below.
for(const path of [...bilingual,'releases/']){
  const zh=chineseOnly(read('zh/'+path));
  for(const [bad,good] of Object.entries(rejected))
    assert.ok(!hasRejected(zh,bad),`zh/${path}: "${bad}" is a rejected rendering — use "${good}"`);
  // A Chinese sentence does not end on an ASCII full stop.
  assert.doesNotMatch(zh,/[一-鿿\d]\.<\/p>/,'zh/'+path+': Chinese sentence ends with an ASCII period');
}
const workbenchSource=readFileSync(new URL('../src/scripts/workbench.ts',import.meta.url),'utf8');
for(const [bad,good] of Object.entries(rejected))
  assert.ok(!hasRejected(workbenchSource,bad),`workbench.ts: "${bad}" is a rejected rendering — use "${good}"`);

// --- 2026-09-22 evidence batch --------------------------------------------------
// The handoff's hard lines, each pinned to the concrete way it could break.
const ev=JSON.parse(readFileSync(new URL('../src/data/evidence-update.json',import.meta.url),'utf8'));
const pageOf=p=>readFileSync(new URL(DIST+''+p+'index.html',import.meta.url),'utf8');
const everyPage=['','data-use/',...topicPages.map(([s])=>'topics/'+s+'/')].flatMap(p=>p==='data-use/'?[p]:[p,'zh/'+p]);
// Only sources with a recorded aggregate_preview decision. L-FAME was excluded
// from this batch and carries no result here; the 2026-09-23 batch publishes its
// status, so its name may appear — with no figure, which the holds check pins.
assert.deepEqual(Object.keys(ev.results).sort(),['alphawaves','eesm23','phantom'],'only sources with a recorded aggregate_preview decision');
assert.ok(!JSON.stringify(ev).match(/L-FAME|lfame/i),'the evidence export carries no L-FAME result');
// No per-person value. EESM23: the in-ear and scalp minima and maxima of a 10-person cohort.
// Alpha Waves: its per-person minima, maxima, medians and quartiles (balanced accuracy,
// macro F1, and the paired difference), none of which the export carries. Its all-16
// macro-F1 lower quartile, 59.7%, is left out: it equals an EESM23 interval bound here.
// Since 2026-10-04 the page also carries #v9-montage, whose every figure is a leaf of the v9 CSVs, the v9
// JSON or experiments.json (re-read by the topic data-fig loop; its figure-like tokens are pinned to those
// files in the v9 topics block below). 33.3% is a v9 interval bound there (REVE Base, BETA, eight
// electrodes), so the per-person check reads the page without that section, which must be one section.
const withoutV9Montage=html=>{const a=html.indexOf('<section class="topic-section fm-topic" id="v9-montage"');
  if(a<0)return html;const b=html.indexOf('</section>',a);assert.equal(html.slice(a+8,b).indexOf('<section'),-1,'#v9-montage nests no section');
  return html.slice(0,a)+html.slice(b);};
for(const p of ['topics/fewer-electrodes/','zh/topics/fewer-electrodes/']){
  assert.doesNotMatch(withoutV9Montage(pageOf(p)),/34\.8%|70\.9%|54\.4%|81\.6%|52\.2%|73\.3%/,p+': an individual person\'s score leaked');
  assert.doesNotMatch(withoutV9Montage(pageOf(p)),/80\.0%|90\.0%|100\.0%|65\.0%|33\.3%|79\.2%|67\.0%|89\.9%|−40\.0 pp|\+30\.0 pp|\+10\.0 pp/,p+': an individual Alpha Waves score leaked');
}
for(const [label,html] of [['en',pageOf('topics/fewer-electrodes/')],['zh',pageOf('zh/topics/fewer-electrodes/')]]){
  assert.match(html,/79\.5%/,label+': four posterior electrodes');
  assert.match(html,/77\.9%/,label+': all sixteen electrodes');
  assert.match(html,/−1\.6 pp/,label+': paired difference, all sixteen minus four');
  assert.match(html,/−10\.0 (?:to|至) \+6\.8 pp/,label+': its interval, which spans zero');
  assert.match(html,/Grégoire Cattan/,label+': dataset authors credited');
  assert.match(html,/zenodo\.2605110/,label+': the Zenodo record is credited');
  assert.match(html,/hal-02086581/,label+': the primary report is credited');
  assert.match(html,/recording 07|第 07 份/,label+': the recording the author loader excludes is named');
  // Every "fewer is better" phrase must sit inside a negation.
  for(const m of html.matchAll(/fewer electrodes (?:are )?(?:generally )?better|电极越少(?:一般)?越好/g))
    assert.match(html.slice(Math.max(0,m.index-60),m.index),/not|neither|不能说明/,label+': "'+m[0]+'" reads as a claim');
}
assert.match(pageOf('topics/fewer-electrodes/'),/not two headsets/,'software subsets are not devices');
// Alpha Waves figures stay on their own page. 79.5% is also a legitimate interval
// bound on dry-vs-wet, so only the difference is checked elsewhere. Since
// 2026-10-01 −1.6 pp is also LoRA minus last block, so on the page that carries
// the adaptation section — calibration-budget until 2026-10-02, model-adaptation
// since — it may appear only inside that section. calibration-budget now has no
// exemption at all.
for(const p of everyPage.filter(p=>!p.includes('fewer-electrodes')&&p!=='data-use/')){
  let html=pageOf(p);
  if(p.includes('model-adaptation')){
    const a=html.indexOf('id="adaptation"'),b=html.indexOf('id="methods-and-limits"');
    assert.ok(a>0&&b>a,p+': the adaptation section must render before methods and limits');
    html=html.slice(0,a)+html.slice(b);
  }
  // Since 2026-10-02 77.9% is also the YSU extension's coverage under the global
  // rule (748 / 960) on when-not-to-act. There it may appear only inside the
  // non-control section, and only as the percentage printed under that count.
  if(p.includes('when-not-to-act')){
    const a=html.indexOf('id="non-control"'),b=html.indexOf('id="methods-and-limits"');
    assert.ok(a>0&&b>a,p+': the non-control section must render before methods and limits');
    const sec=html.slice(a,b);
    // −1.6 pp has no reading in this section at all.
    assert.doesNotMatch(sec,/−1\.6 pp/,p+': −1.6 pp (Alpha Waves) inside the non-control section');
    for(const m of sec.matchAll(/77\.9%/g))
      assert.match(sec.slice(Math.max(0,m.index-60),m.index),/>748 \/ 960<\/span><span class="interval">$/,p+': 77.9% in the non-control section may only be the coverage 748 / 960');
    html=html.slice(0,a)+html.slice(b);
  }
  assert.doesNotMatch(html,/−1\.6 pp|77\.9%/,p+': Alpha Waves figures belong on the fewer-electrodes page');
}
for(const [label,html] of [['en',pageOf('topics/fewer-electrodes/')],['zh',pageOf('zh/topics/fewer-electrodes/')]]){
  assert.match(html,/53\.6%/,label+': in-ear balanced accuracy');
  assert.match(html,/69\.0%/,label+': scalp balanced accuracy');
  assert.match(html,/\+15\.4 pp/,label+': paired difference in percentage points');
  assert.match(html,/11,674/,label+': usable-data coverage travels with the scores');
  assert.match(html,/10\.1038\/s41597-025-04579-8/,label+': the study paper is credited');
  assert.match(html,/10\.18112\/openneuro\.ds005178/,label+': the dataset record is credited');
  assert.match(html,/Yousef Rezaei Tabar/,label+': the dataset\'s own author list, not only the paper\'s');
}
assert.match(pageOf('topics/fewer-electrodes/'),/Six scalp electrodes, not eight/,'mastoid slots are not scalp sensors');
// Phantom: R² as measured. Negative, dimensionless, never a percent.
for(const p of ['topics/on-the-move/','zh/topics/on-the-move/']){
  const html=pageOf(p);
  for(const v of ['−795.772','−596.820','−142.832','0.567']) assert.ok(html.includes(v),p+': predictive R² '+v+' must appear as measured');
  assert.doesNotMatch(html,/−?\d+\.\d{3}%/,p+': correlation and R² are dimensionless, never percent');
}
assert.match(pageOf('topics/on-the-move/'),/Neither column is accuracy/,'phantom metrics must be distinguished from accuracy');
// The 2026-09-22 file keeps its roadmap as released: 'planned' was true then.
// Since 2026-10-01 the page shows measured results in its place (checked in the
// adaptation block below), and still must not borrow the old pilot's figures.
// Since 2026-10-02 that page is model-adaptation; calibration-budget, which held
// it until then, stays under the same exclusions.
assert.equal(ev.roadmap.peft.status,'planned');
for(const p of ['topics/calibration-budget/','zh/topics/calibration-budget/','topics/model-adaptation/','zh/topics/model-adaptation/']){
  const html=pageOf(p);
  // Its exact two-decimal figures. One decimal collides: 65.1% is a CCA value on calibration-budget.
  assert.doesNotMatch(html,/56\.34|65\.05/,p+': the unapproved partial-fine-tuning pilot must not appear');
  // Case-insensitive: the first version missed a sentence-initial "In progress".
  assert.doesNotMatch(html,/\bin progress\b|\bunderway\b|\b(?:is|now) running\b|进行中|正在运行|已开始/i,p+': nothing on this page is described as still running');
  if(p.includes('model-adaptation')) assert.ok(html.includes('38,400')&&html.includes('5,819,936'),p+': engineering parameter counts');
  assert.doesNotMatch(html,/0\.87|\b1 s(econd)?\b|约 ?1 秒/,p+': the synthetic smoke-test runtime is not a training cost');
}

// --- 2026-09-23 clinical batch ---------------------------------------------
// A clinical cohort, so the checks are about what must not be claimed and what
// must not appear, not only about the figures being right.
const cl=JSON.parse(readFileSync(new URL('../src/data/clinical-update.json',import.meta.url),'utf8'));
assert.deepEqual(Object.keys(cl.results),['ds004584'],'only the reviewed clinical source carries numbers');
assert.deepEqual(cl.status_only.map(e=>e.id).sort(),['ds004902','lfame'],'both status-only sources stay listed');
for(const [label,html] of [['en',pageOf('topics/clinical-groups/')],['zh',pageOf('zh/topics/clinical-groups/')]]){
  assert.match(html,/71\.7%/,label+': the EEG model score');
  assert.match(html,/55\.0%/,label+': the confound comparator score');
  assert.match(html,/63\.5%–79\.3%/,label+': the EEG interval');
  assert.match(html,/46\.9%–63\.6%/,label+': the comparator interval');
  assert.match(html,/\+16\.6 pp/,label+': the gap between them');
  assert.match(html,/0\.76/,label+': AUROC travels with the score');
  // The comparator is on the page, and is marked as not a model.
  assert.match(html,label==='en'?/not an EEG model/:/不是 EEG 模型/,label+': the comparator must be marked');
  // The claim boundary, in the page's own language.
  assert.match(html,label==='en'?/Not a diagnosis/:/不是诊断/,label+': the claim boundary must be stated');
  assert.doesNotMatch(html,/diagnostic accuracy(?!,| —)|screening tool(?!,)/,label+': no diagnostic claim');
  assert.doesNotMatch(html,/可以诊断|用于诊断|诊断准确率(?!，)/,label+': no diagnostic claim in Chinese');
  // A diagnosis-specific cohort's demographic profile is never published.
  assert.doesNotMatch(html,/68\.5|70\.9|68\.53|70\.92/,label+': the per-group age means must not appear');
  assert.match(html,/IRB 201707828/,label+': the ethics approval is cited');
  assert.match(html,/10\.1136\/jnnp-2022-330154/,label+': the cohort study is credited');
}
// The released medical disclaimer, the most safety-relevant sentence on the
// page, is in Chinese on the Chinese page, with the released English beside it.
{
  const zh=pageOf('zh/topics/clinical-groups/');
  assert.ok(zh.includes('<p class="protocol-note">公开数据集上的研究结果：不是诊断，不是诊断准确率，也不是医疗器械或医疗建议。'),'zh: the medical disclaimer must be in Chinese');
  assert.ok(zh.includes('<span lang="en">'+cl.medical_disclaimer+'</span>'),'zh: the released English disclaimer stays beside it, marked English');
}
// Home section order (owner, 2026-10-07): the core matrix right under the title, then the evidence behind each
// score, then the questions, holds, directory and method notes.
for(const path of ['','zh/']){
  const home=pageOf(path);
  const at=['overview','benchmarks','topics','holds','directory','methods'].map(id=>home.indexOf('<section id="'+id+'"'));
  assert.ok(at.every(i=>i>0),(path||'/')+': every home section renders');
  assert.ok(at.every((i,k)=>k===0||i>at[k-1]),(path||'/')+': home sections in the order matrix, evidence, questions, holds, directory, methods');
  assert.ok(home.indexOf('class="masthead"')<at[0],(path||'/')+': the core matrix comes right after the masthead');
}
// Holds: three of them, stated without numbers, on both home pages.
for(const [label,path] of [['en',''],['zh','zh/']]){
  const home=pageOf(path);
  // Holds end where the next section starts (the directory band since the 2026-10-07 reorder).
  const hs=home.indexOf('id="holds"'), holds=home.slice(hs,home.indexOf('<section',hs+1));
  assert.ok(holds.length>400,label+': the holds section must render');
  for(const word of label==='en'?['No score','Held','Described, not scored']:['没有分数','暂缓','只有描述，没有评分'])
    assert.ok(holds.includes(word),label+': hold state "'+word+'" must be shown');
  // A hold has no result. No percentage, and no decimal figure, inside the cards.
  const cards=holds.slice(holds.indexOf('hold-grid'));
  assert.doesNotMatch(cards,/\d+(?:\.\d+)?%|\d\.\d/,label+': a hold must not carry a figure');
  // A card says what is held and why, with no date (owner decision 2026-10-08): the date each hold was
  // opened is in the full register, one click away.
  assert.doesNotMatch(holds,/Held since|起暂缓|<time\b/,label+': a hold card carries no date; the register does');
  assert.ok(holds.includes(label==='en'?'href="/releases/#holds"':'href="/zh/releases/#holds"'),label+': the holds register must be linked');
}
// The withheld six-person descriptors appear nowhere, in any locale.
const lfameMedians=['0.3540','0.3849','0.2303','0.2655','0.2319'];
// The route-2 page (2026-10-07) carries contrasts in pp whose full-precision raw values, inside data-fig attributes
// that the data-fig loop holds to the route-2 export, begin "0.230" and "0.231"; the later-sessions page's raw values
// (a 35.4% interval bound, 0.0052730… and the like) contain them too. Those attributes are set aside here, and
// everything printed, and every other attribute, is still read.
for(const p of [...everyPage,'topics/clinical-groups/','zh/topics/clinical-groups/'])
  for(const v of lfameMedians)
    assert.ok(!pageOf(p).replace(/ data-fig="(?:shared-representation|later-sessions)-update\.json\|[^"]*"/g,'').includes(v.slice(0,5)),p+': a withheld L-FAME descriptor appeared');

// --- 2026-09-27 site update: when not to act, and the release log ----------
// The abstention topic: every figure from the reviewed idle protocol, and a
// roadmap that is a plan — no figure, no borrowed number, no word that reads
// as done.
const idleTrack=data.tracks.find(t=>t.id==='idle');
const [,idleN,cmdN]=idleTrack.observations.match(/(\d+) idle \/ (\d+) command/).map(Number);
for(const [label,path] of [['en','topics/when-not-to-act/'],['zh','zh/topics/when-not-to-act/']]){
  const html=pageOf(path);
  for(const r of idleTrack.rows){
    assert.ok(html.includes(`${Math.round(r.y/100*cmdN)} / ${cmdN}`),label+': '+r.name+' command count');
    assert.ok(html.includes(`${Math.round(r.x/100*idleN)} / ${idleN}`),label+': '+r.name+' false-activation count');
    assert.ok(html.includes(r.y.toFixed(1)+'%'),label+': '+r.name+' detection percentage');
  }
  // Abstention travels with every row: the number of people who always abstained.
  const abstainCells=[...html.matchAll(/class="metric">\d<\/span><span class="interval">(?:of 4 people|共 4 名被试)</g)].length;
  assert.equal(abstainCells,idleTrack.rows.length,label+': every method shows how many people always abstained');
  assert.ok(html.includes('href="/data-use/#small-cohorts"'),label+': the four-person arithmetic must be linked');
  const road=html.slice(html.indexOf('id="decision-research"'),html.indexOf('class="topic-switcher"'));
  assert.ok(road.length>2000,label+': the roadmap section must render');
  // Since 2026-10-04 (owner approval) route 1 has been run; its results are their own section,
  // #reliable-decisions, before this one. Since 2026-10-07 (owner approval) route 2 has been run too; its
  // results are their own question, /topics/shared-encoder/. The roadmap stays a plan: each route carries
  // its own status, route 3 is not run, and nothing in the section is a figure.
  assert.match(road,/data-status="plan"/,label+': the roadmap is a plan');
  assert.match(road,/data-run-status="routes-1-2-run"/,label+': the roadmap says routes 1 and 2 have been run');
  assert.match(road,label==='en'?/Status: the first two routes have been run\. The first route’s results are in the section above, the second’s on their own page\. The third route has not been run\./
                                :/状态：前两条路线已经运行。第一条的结果见上一节，第二条的结果在单独的页面上；第三条路线尚未运行。/,label+': the roadmap states each route\'s status in words');
  assert.doesNotMatch(road,/No experiment in this section has been run|本节中的实验都尚未运行|The other two routes have not been run|另外两条路线尚未运行/,label+': an old status line');
  const routes=[...road.matchAll(/<li data-route="([^"]+)" data-route-status="([^"]+)">([\s\S]*?)<\/li>/g)];
  assert.deepEqual(routes.map(m=>[m[1],m[2]]),[['reliable-decisions','run'],['one-representation','run'],['questions-in-language','not_run']],label+': one status per route, routes 1 and 2 run, route 3 not run');
  const [r1,r2,...later]=routes.map(m=>m[3]);
  assert.match(r1,label==='en'?/<p class="eyebrow">First · Run · results above<\/p>/:/<p class="eyebrow">首先 · 已运行 · 结果见上一节<\/p>/,label+': route 1 says it was run');
  assert.ok(r1.includes(`href="${label==='zh'?'/zh':''}/topics/when-not-to-act/#reliable-decisions"`),label+': route 1 links its results');
  // The plan promised acceptance per class and reliability; the run published neither (review of 2026-10-05).
  assert.match(r1,label==='en'?/<p class="route-run-note">[^<]*Not published: acceptance per class and reliability-diagram bins\.<\/p>/
                              :/<p class="route-run-note">[^<]*没有发布：各类别的接受率和可靠性图的分箱。<\/p>/,label+': route 1 says which planned measures it did not publish');
  // Route 2 (2026-10-07): run, its results on their own page, linked; its run note names where it ran and that the
  // E2-sleep arm ran after the other results were known.
  assert.match(r2,label==='en'?/<p class="eyebrow">Then · Run · results on their own page<\/p>/:/<p class="eyebrow">随后 · 已运行 · 结果在单独的页面上<\/p>/,label+': route 2 says it was run');
  assert.ok(r2.includes(`<p class="route-results"><a href="${label==='zh'?'/zh':''}/topics/shared-encoder/">`),label+': route 2 links its page');
  assert.match(r2,label==='en'?/<p class="route-run-note">Run on motor imagery \(OpenBMI\) and sleep \(BOAS, with EESM19 as a crude replication\)\. One secondary arm, CBraMod adapted by LoRA on sleep, ran after the other results were known; its design was fixed beforehand\.<\/p>/
                              :/<p class="route-run-note">在运动想象（OpenBMI）和睡眠（BOAS，EESM19 作粗略重复）上运行。有一项次要设置——在睡眠上用 LoRA 适配 CBraMod——是在其他结果已知之后才运行的；它的设计事先已定。<\/p>/,label+': route 2 says where it ran and that E2 sleep ran last');
  for(const r of later){
    assert.match(r,label==='en'?/<p class="eyebrow">Later · Not run<\/p>/:/<p class="eyebrow">之后 · 尚未运行<\/p>/,label+': route 3 is not run');
    assert.doesNotMatch(r,/href=|route-results|reliable-decisions|shared-encoder/,label+': a route that has not run links no result');
  }
  assert.ok(html.indexOf('id="reliable-decisions"')>0&&html.indexOf('id="reliable-decisions"')<html.indexOf('id="decision-research"'),label+': the results section comes before the roadmap, outside its slice');
  // A plan carries no figure: no percentage, no decimal, no speed-up, no ms.
  // Visible text only: arXiv identifiers in link targets are not figures.
  const roadText=road.replace(/<[^>]+>/g,' ');
  assert.doesNotMatch(roadText,/\d+(?:\.\d+)?\s?%|\d\.\d|\d+(?:\.\d+)?\s?[×x]\b|\d+\s?ms\b/,label+': a figure appeared in the roadmap');
  assert.ok(!road.includes('data-fig'),label+': the roadmap prints no data figure');
  // Wording that would read as done, for routes that are not.
  assert.doesNotMatch(road,/calibrated policy|measured uncertainty|经过校准的策略|经过评测的不确定性|we (?:have )?(?:trained|measured|built)/i,label+': the roadmap must not read as completed work');
  // "Jev-style" is prominent by the maintainer's choice (heading, title, card).
  // Wherever it is, the page says what it is not: no Jev integration, no Jev
  // model that reads EEG, and that route 1's results need no such model.
  assert.match(road,/<h2[^>]*>Jev-style/,label+': the roadmap heading names the research track');
  // Since 2026-10-07 route 2 trained models of its own, so the scope no longer says none was trained; it says what
  // they are (one shared encoder: small EEGNets, CBraMod frozen or adapted; questions given by an identifier, never in
  // language). The review of 2026-10-07 had it name CBraMod too, not small encoders only.
  assert.match(html,label==='en'
    ?/This is not an integration with Jev and not a Jev model that reads EEG\. The first route needs no such model: its results, in the section above, rescore saved outputs of models this site already publishes\. The second trained models that share one encoder \(small EEGNets from scratch, and CBraMod frozen or adapted by LoRA\) and are given each question by an identifier, never in language; its results have their own page\./
    :/这里既没有接入 Jev，也不是能读 EEG 的 Jev 模型。第一条路线用不到这样的模型：上一节的结果，是对本站已发布模型保存下来的输出重新评分得到的。第二条路线训练了共用一个编码器的模型（从头训练的小型 EEGNet，以及冻结或用 LoRA 适配的 CBraMod），问题只以标识给出，从不用语言；它的结果有单独的页面。/,label+': the Jev scope sentence must stand beside the name');
  assert.doesNotMatch(html,/not a model BCI Report has trained|更不是本站训练出的模型/i,label+': the old scope said no model was trained');
  assert.doesNotMatch(html,/There are no results here yet|目前还没有任何结果/,label+': the old no-results scope sentence');
  assert.ok(road.indexOf('research-scope')<road.indexOf('route-list'),label+': the scope sentence comes before the routes');
}
// A source on hold in any review manifest is not named on any page until the
// hold is lifted — the rule Alpha Waves and the YSU pilot were held under. Read
// from the manifests themselves, so a new hold is covered without a new line here.
const manifests=['publication_review_20260922/evidence-release-manifest.json','publication_review_20260923/clinical-release-manifest.json','publication_review_20260927/context-release-manifest.json',
  'publication_review_20261001/adaptation-release-manifest.json','publication_review_20261002/extension-release-manifest.json',
  'publication_review_20261003/large-source-release-manifest.json']
  .map(f=>JSON.parse(readFileSync(new URL('../../research/'+f,import.meta.url),'utf8')));
const held=manifests.flatMap(m=>m.sources).filter(x=>x.decision==='hold');
const allPages=[...everyPage,...['screen-to-vr','when-not-to-act'].flatMap(s=>['topics/'+s+'/','zh/topics/'+s+'/']),'releases/','zh/releases/'];
for(const h of held) for(const p of allPages){
  assert.ok(!pageOf(p).includes(h.name),p+': held source '+h.id+' is named');
  assert.ok(!pageOf(p).includes(h.source.split('/').pop()),p+': held source '+h.id+' is linked');
}
// The release log: every download is listed, and every listed hash is the hash
// of the byte-identical file the site serves.
const {createHash}=await import('node:crypto');
for(const [label,path] of [['en','releases/'],['zh','zh/releases/']]){
  const html=pageOf(path);
  const listed=[...html.matchAll(/<code class="hash" data-file="([^"]+)">([0-9a-f]{64})<\/code>/g)];
  const served=readdirSync(new URL(DIST+'data/',import.meta.url));
  assert.deepEqual(listed.map(m=>m[1]).sort(),[...served].sort(),label+': every served download is listed exactly once');
  for(const [,file,sha] of listed)
    assert.equal(sha,createHash('sha256').update(readFileSync(new URL(DIST+'data/'+file,import.meta.url))).digest('hex'),label+': '+file+' hash on the page is not the served file');
  for(const id of [data.releaseId,topics.release_id,ev.release_id,cl.release_id])
    assert.ok(html.includes(`id="${id}"`),label+': release '+id+' must be listed');
  assert.ok(html.includes(ev.provenance.manifest_sha256)&&html.includes(cl.provenance.manifest_sha256),label+': review manifest hashes are shown');
  assert.match(html,/class="hold-resolved"/,label+': resolved holds stay in the register');
}

// --- 2026-09-27 context batch ------------------------------------------------
const cx=JSON.parse(readFileSync(new URL('../src/data/context-update.json',import.meta.url),'utf8'));
assert.deepEqual(Object.keys(cx.results).sort(),['gait-eeg','vr-pc-p300','ysu-async-ssvep'],'only sources with a recorded aggregate_preview decision');
for(const [label,path] of [['en','topics/screen-to-vr/'],['zh','zh/topics/screen-to-vr/']]){
  const html=pageOf(path);
  for(const v of ['66.0%','63.6%','63.8%','57.2%','61.6%–70.2%','0.732','30,240','30,101']) assert.ok(html.includes(v),label+': PC/VR figure '+v);
  // The one thing this result is not: the cost of the display change.
  assert.match(html,label==='en'?/did not also test each person on the display they were calibrated on/:/没有在被试校准时所用的那种设备上再测一次/,label+': the missing same-display reference is stated');
  assert.match(html,/arXiv:1903\.11297/,label+': the dataset documentation is credited');
  assert.match(html,/Grenoble|格勒诺布尔/,label+': the ethics committee is named');
  // Per-person values of a 21-person cohort: minima, maxima, medians, quartiles.
  assert.doesNotMatch(html,/47\.1%|82\.3%|67\.3%|61\.6%<|72\.8%|49\.6%|79\.9%|65\.0%|0\.423|0\.910|0\.776/,label+': an individual score leaked');
}
for(const [label,path] of [['en','topics/on-the-move/'],['zh','zh/topics/on-the-move/']]){
  const html=pageOf(path);
  for(const v of ['45.4%','50.6%','39.1%–51.7%','44.3%–56.9%','+5.2 pp']) assert.ok(html.includes(v),label+': gait figure '+v);
  assert.match(html,label==='en'?/is not evidence of decoding the brain/:/不能说明解码到了大脑活动/,label+': the gait score is not sold as neural decoding');
  assert.match(html,/H19-038/,label+': the gait ethics approval is cited');
}
// The non-control pilot: accuracy among accepted windows never travels alone.
for(const [label,path] of [['en','topics/when-not-to-act/'],['zh','zh/topics/when-not-to-act/']]){
  const html=pageOf(path);
  const sec=html.slice(html.indexOf('id="non-control"'),html.indexOf('id="methods-and-limits"'));
  assert.ok(sec.length>1500,label+': the non-control section must render');
  for(const v of ['152 / 192','130 / 192','121 / 192','121 / 130','9 / 48','20 / 48','11 / 96']) assert.ok(sec.includes(v),label+': non-control count '+v);
  assert.ok(sec.includes('93.1%')&&sec.includes('67.7%')&&sec.includes('63.0%'),label+': conditional accuracy, coverage and end-to-end rate appear together');
  assert.ok(sec.indexOf('67.7%')<sec.indexOf('93.1%')&&sec.indexOf('63.0%')<sec.indexOf('93.1%'),label+': coverage and end-to-end rate come before conditional accuracy');
  assert.match(sec,/Qinhuangdao|秦皇岛/,label+': the ethics committee is named');
  assert.match(sec,/10\.1080\/27706710\.2024\.2418650/,label+': the data paper is credited');
  assert.match(sec,label==='en'?/not false activations per hour/:/不是每小时的误触发次数/,label+': window rates are not hourly rates');
  // Per-participant range bounds of a four-person pilot.
  assert.doesNotMatch(sec,/47\.9%|97\.9%|83\.9%|58\.3%|16\.7%|68\.8%|8\.3%/,label+': an individual rate leaked');
}

// The published payload stays English. Chinese lives in the display layer only.
for(const file of readdirSync(new URL(DIST+'data/',import.meta.url)))
  assert.equal(/\p{Script=Han}/u.test(readFileSync(new URL(DIST+'data/'+file,import.meta.url),'utf8')),false,
    'dist/data/'+file+': a download must not carry translated text');
assert.equal(existsSync(new URL(DIST+'zh/data-use/index.html',import.meta.url)),false,'/data-use/ stays English-only');
for(const path of bilingual){
  assert.ok(sitemap.includes('<loc>https://bci.report/zh/'+path+'</loc>'),'sitemap must list zh/'+path);
  assert.ok(sitemap.includes('hreflang="zh-Hans" href="https://bci.report/zh/'+path+'"'),'sitemap must pair zh/'+path+' with its alternates');
}

// --- Short answers ----------------------------------------------------------
// Each topic page opens with its question and a two- or three-sentence answer.
// The answer summarises the page: every figure in it must also appear in the
// evidence below, so it can never be the only place a number is stated. The
// FAQPage markup must say exactly what the page says.
const visible=html=>html.replace(/<head>[\s\S]*?<\/head>/,'').replace(/<script[\s\S]*?<\/script>/g,'').replace(/<[^>]+>/g,' ').replace(/&amp;/g,'&').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/\s+/g,' ');
const numbers=s=>[...s.matchAll(/\d[\d,]*(?:\.\d+)?/g)].map(m=>m[0]);
// CHECK_ONLY=<slug> narrows this block to one page while others are being written.
for(const [slug,q] of topicPages.filter(([s])=>!process.env.CHECK_ONLY||s===process.env.CHECK_ONLY)) for(const [label,path,question] of [['en','topics/'+slug+'/',q],['zh','zh/topics/'+slug+'/',zhTitles[slug]]]){
  const html=pageOf(path);
  const start=html.indexOf('<section class="short-answer"'),end=html.indexOf('</section>',start);
  assert.ok(start>0,label+'/'+slug+': the short answer must render');
  const answer=html.slice(start,end);
  const figs=[...answer.matchAll(/class="fig">([^<]+)</g)].map(m=>m[1]);
  assert.ok(figs.length>0,label+'/'+slug+': a short answer states at least one figure');
  const rest=visible(html.slice(0,start)+html.slice(end));
  for(const f of figs) for(const n of numbers(f))
    assert.ok(rest.includes(n),label+'/'+slug+': "'+f+'" in the short answer appears nowhere else on the page');
  assert.ok(html.includes('<title>'+question),label+'/'+slug+': the <title> leads with the question');
  const desc=html.match(/<meta name="description" content="([^"]*)"/)[1];
  assert.ok(desc.length>40&&desc.length<=320,label+'/'+slug+': meta description must answer in one or two sentences ('+desc.length+' chars)');
  if(label==='en'){
    const ld=JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
    const faq=ld['@graph'].find(n=>n['@type']==='FAQPage');
    assert.ok(faq,slug+': FAQPage markup is required');
    assert.equal(faq.mainEntity[0].name.replace(/'/g,'&#39;'),question,slug+': the marked-up question is the h1');
    const printed=answer.slice(answer.indexOf('<p>')).replace(/<[^>]+>/g,'').replace(/&amp;/g,'&').replace(/&#39;/g,"'").replace(/&quot;/g,'"').trim();
    assert.equal(faq.mainEntity[0].acceptedAnswer.text,printed,slug+': the marked-up answer is the printed answer');
  }
}

// --- Dataset, method and API pages; agent files ------------------------------------
// The entity pages add no number. Every figure carries data-fig="<file>|<format>|<raw>":
// the raw value must be a leaf of that served file, and the printed text must be
// that leaf in that format. An average, difference or rank computed for the page
// has no leaf to match.
const walkDist=(dir,out=[])=>{for(const f of readdirSync(new URL(dir,DIST))){const rel=dir+f;if(f==='_astro'||f==='data')continue;
  if(existsSync(new URL(rel+'/',DIST))&&!/\.\w+$/.test(f))walkDist(rel+'/',out);else out.push(rel);}return out;};
const distFiles=walkDist('');
const htmlPages=distFiles.filter(f=>f.endsWith('index.html'));
const leaves=new Map();
// A CSV's leaves are its numeric cells below the header row. RFC 4180 quoting:
// the results files quote attribution strings that carry commas.
const csvRows=text=>{const rows=[];let row=[],cell='',quoted=false;
  for(let i=0;i<text.length;i++){const ch=text[i];
    if(quoted){if(ch==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(ch==='"')quoted=false;else cell+=ch;}
    else if(ch==='"')quoted=true;else if(ch===','){row.push(cell);cell='';}
    else if(ch==='\n'||ch==='\r'){if(ch==='\r'&&text[i+1]==='\n')i++;row.push(cell);rows.push(row);row=[];cell='';}
    else cell+=ch;}
  if(cell!==''||row.length){row.push(cell);rows.push(row);}return rows;};
const leavesOf=file=>{if(!leaves.has(file)){const set=new Set();const walk=v=>{if(typeof v==='number')set.add(v);else if(v&&typeof v==='object')Object.values(v).forEach(walk);};
  const text=readFileSync(new URL('data/'+file,DIST),'utf8');
  if(file.endsWith('.csv')){for(const row of csvRows(text).slice(1))for(const c of row)if(c.trim()!==''&&Number.isFinite(Number(c)))set.add(Number(c));}
  else walk(JSON.parse(text));
  leaves.set(file,set);}return leaves.get(file);};
const fmt={pct1:r=>(r*100).toFixed(1)+'%',pct1raw:r=>r.toFixed(1)+'%',pct2raw:r=>r.toFixed(2)+'%',pp1:r=>(r>=0?'+':'−')+Math.abs(r*100).toFixed(1)+' pp',
  sgn1:r=>(r>=0?'+':'−')+Math.abs(r*100).toFixed(1),sgn3:r=>(r>=0?'+':'−')+Math.abs(r).toFixed(3),
  // A second decimal where one would read as zero (review of 2026-10-05): −0.03 pp, a bound of +0.02, a coverage of 0.05%.
  pp2:r=>(r===0?'':r>0?'+':'−')+Math.abs(r*100).toFixed(2)+' pp',sgn2:r=>(r===0?'':r>0?'+':'−')+Math.abs(r*100).toFixed(2),pct2:r=>(r*100).toFixed(2)+'%',
  auc3:r=>r.toFixed(3),auc2:r=>r.toFixed(2),num3:r=>r.toFixed(3).replace(/^-/,'−'),count:r=>r.toLocaleString('en-US'),s1:r=>r.toFixed(1)+' s',
  m2:r=>(r/1e6).toFixed(2)+'M',
  // Route 2 (2026-10-07): values already in percentage points, two decimals; a step time in seconds as milliseconds.
  ppr2:r=>(r===0?'':r>0?'+':'−')+Math.abs(r).toFixed(2)+' pp',sgr2:r=>(r===0?'':r>0?'+':'−')+Math.abs(r).toFixed(2),ms2:r=>(r*1000).toFixed(2)+' ms',
  // The later-sessions page: values spanning many decades — a whole number with thousands separators, or three
  // significant digits where three decimals would print a non-zero value as 0.000 (entities.ts wideFmt).
  int0:r=>Math.round(r).toLocaleString('en-US').replace(/^-/,'−'),sig3:r=>r.toPrecision(3).replace(/^-/,'−')};
// The token checks of the earlier batches read every format but these: their pages print none, and a later
// format applied to their values would only widen what those checks accept.
const fmtEarlier=Object.entries(fmt).filter(([k])=>!['ppr2','sgr2','ms2','int0','sig3'].includes(k)).map(([,g])=>g);
// Protocol pages (/protocols/, since 2026-10-02) are held to every entity-page
// check below: figures re-read, bilingual parity, hreflang, CSP, glossary,
// sitemap and llms.txt. Their own checks follow in the protocol block.
const entityPages=htmlPages.filter(f=>/(?:^|\/)(?:datasets|methods|protocols)\//.test(f));
assert.ok(entityPages.length>=2*(16+9+2+1+data.tracks.length),'dataset, method and protocol pages, both languages');
let figsChecked=0;
for(const f of entityPages){
  const html=readFileSync(new URL(f,DIST),'utf8');
  for(const [,file,format,raw,text] of html.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)){
    const v=Number(raw);
    assert.ok(leavesOf(file).has(v),f+': '+raw+' is not a value in '+file);
    assert.equal(text,fmt[format](v),f+': '+file+' '+raw+' printed as "'+text+'"');
    figsChecked++;
  }
}
assert.ok(figsChecked>500,'the entity pages must carry their figures ('+figsChecked+')');
// Both languages, every figure equal, hreflang reciprocal, CSP, glossary.
const entityBilingual=entityPages.filter(f=>!f.startsWith('zh/')).map(f=>f.replace(/index\.html$/,''));
for(const path of [...entityBilingual,'api/']){
  const en=read(path),zh=read('zh/'+path);
  const figures=html=>[...html.matchAll(/class="(?:metric|num|fig)">([^<]+)</g)].map(m=>m[1]);
  assert.deepEqual(figures(zh),figures(en),'zh/'+path+': every number must equal the English page, in the same order');
  assert.ok(en.includes(`hreflang="zh-Hans" href="https://bci.report/zh/${path}"`)&&zh.includes(`hreflang="en" href="https://bci.report/${path}"`),path+': reciprocal hreflang');
  assert.doesNotMatch(zh,/application\/ld\+json/,'zh/'+path+': structured data on the English canonical only');
  for(const html of [en,zh]){
    assert.doesNotMatch(html,/\sstyle="|<style[\s>]|\son(?:click|load|error|change|submit)=/,path+': the CSP forbids inline style and handlers');
  }
  const zhText=chineseOnly(zh);
  for(const [bad,good] of Object.entries(rejected)) assert.ok(!hasRejected(zhText,bad),`zh/${path}: "${bad}" is a rejected rendering — use "${good}"`);
  assert.doesNotMatch(zhText,/[一-鿿\d]\.<\/p>/,'zh/'+path+': Chinese sentence ends with an ASCII period');
  assert.ok(sitemap.includes('<loc>https://bci.report/'+path+'</loc>')&&sitemap.includes('<loc>https://bci.report/zh/'+path+'</loc>'),path+': sitemap entry in both languages');
}
// Only reviewed results reach an entity page: no status-only or held source has one.
for(const id of [...cl.status_only,...cx.status_only].map(x=>x.id))
  assert.ok(!entityPages.some(f=>f.includes('/'+id+'/')),id+': a status-only source must not get a dataset page');
// The API page lists exactly the files served.
const apiPage=read('api/');
const apiFiles=[...apiPage.matchAll(/<a href="\/data\/([^"]+)" download><code>/g)].map(m=>m[1]).sort();
assert.deepEqual(apiFiles,readdirSync(new URL('data/',DIST)).sort(),'the data API page lists every served file exactly once');
// Every page has its Markdown copy, and every figure on the page survives into it.
for(const f of htmlPages){
  const md=f.replace(/index\.html$/,'index.md');
  assert.ok(distFiles.includes(md),f+': Markdown copy missing');
  const html=readFileSync(new URL(f,DIST),'utf8'),copy=readFileSync(new URL(md,DIST),'utf8');
  assert.ok(html.includes(`rel="alternate" type="text/markdown" href="/${md}"`),f+': must link its Markdown copy');
  for(const [,v] of html.matchAll(/class="(?:metric|num|fig)">([^<]+)</g)) assert.ok(copy.includes(v.replace(/&amp;/g,'&')),md+': figure "'+v+'" missing from the copy');
}
// llms.txt: every question with its short answer, every dataset and method page.
const llms=readFileSync(new URL('llms.txt',DIST),'utf8');
assert.match(llms,/^# BCI Report\n\n> /,'llms.txt: H1 then a blockquote summary (llmstxt.org)');
for(const [slug] of topicPages){
  assert.ok(llms.includes('https://bci.report/topics/'+slug+'/index.md'),'llms.txt: '+slug);
  const ans=pageOf('topics/'+slug+'/').match(/<section class="short-answer"[\s\S]*?<p>([\s\S]*?)<\/p>/)[1].replace(/<[^>]+>/g,'').replace(/&#39;/g,"'").replace(/&amp;/g,'&').slice(0,60);
  assert.ok(llms.replace(/\*\*/g,'').includes(ans),'llms.txt: the short answer for '+slug);
}
for(const p of entityBilingual) assert.ok(llms.includes('https://bci.report/'+p+'index.md'),'llms.txt: '+p);
// --- 2026-10-01 adaptation batch and site update -----------------------------
const ad=JSON.parse(readFileSync(new URL('../src/data/adaptation-update.json',import.meta.url),'utf8'));
assert.deepEqual(Object.keys(ad.results),['eegmat-labram-adaptation'],'only the reviewed adaptation source carries numbers');
assert.deepEqual(ad.status_only.map(e=>e.id),['bnci2015-001-crossday'],'the next-day experiment stays status only');
const adr=ad.results['eegmat-labram-adaptation'];
const pct1=v=>(v*100).toFixed(1)+'%', pp1=v=>(v>=0?'+':'−')+Math.abs(v*100).toFixed(1)+' pp';
const ivp=(iv,zh)=>`${iv[0]>=0?'+':'−'}${Math.abs(iv[0]*100).toFixed(1)} ${zh?'至':'to'} ${iv[1]>=0?'+':'−'}${Math.abs(iv[1]*100).toFixed(1)} pp`;
// The handoff's headline figures, so a changed export cannot pass by changing the page with it.
assert.deepEqual(adr.arms.map(a=>pct1(a.balanced_accuracy.mean)),['56.6%','65.7%','64.1%'],'the audited arm means');
const matrixLabram=data.tracks.find(t=>t.id==='arithmetic-rest').rows.find(r=>r.name==='LaBraM'&&r.mode==='Frozen encoder + ridge head');
// Since 2026-10-02 the adaptation result and the next-day statuses are their own
// topic, model-adaptation (owner approved); every check below moved with them.
// calibration-budget keeps its SSVEP question and two figure-free notes, at the
// old anchors, that send readers there.
const cxs=JSON.parse(readFileSync(new URL('../src/data/context-update.json',import.meta.url),'utf8')).status_only.find(e=>e.id==='stieger-longitudinal');
assert.equal(cxs.feasibility.people,1,'the cross-session slot says "one person"; update both together if this changes');
assert.equal(cxs.scores_published,false,'the cross-session source stays status only');
const armPct=id=>pct1(adr.arms.find(a=>a.id===id).balanced_accuracy.mean);
const unent=s=>s.replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/&amp;/g,'&');
// What a reader is told this evidence is, wherever it is summarised (card, snippet, short answer, entity group).
const adLabel={en:/new people, same task, zero labels from the test person/i,zh:/新被试、同一任务、不使用测试被试的任何标签/};
const nextLabel={en:/next[- ]day/i,zh:/次日|第二天/};
for(const [label,path] of [['en','topics/model-adaptation/'],['zh','zh/topics/model-adaptation/']]){
  const html=pageOf(path),zh=label==='zh',prefix=zh?'/zh':'';
  const sec=html.slice(html.indexOf('id="adaptation"'),html.indexOf('id="methods-and-limits"'));
  assert.ok(html.indexOf('id="adaptation"')>0&&sec.length>4000,label+': the adaptation section renders before methods and limits');
  for(const a of adr.arms){
    assert.ok(sec.includes('<div class="reading">'+pct1(a.balanced_accuracy.mean)+'</div>'),label+': '+a.id+' score on its card');
    assert.ok(sec.includes(pct1(a.balanced_accuracy.bootstrap_95[0])+'–'+pct1(a.balanced_accuracy.bootstrap_95[1])),label+': '+a.id+' interval');
    assert.ok(sec.includes(a.trainable_parameters.toLocaleString('en-US')),label+': '+a.id+' trainable parameters');
    assert.ok(sec.includes(a.training_seconds_15_fits.toFixed(1)+' s'),label+': '+a.id+' training time');
    for(const s of a.balanced_accuracy.per_seed_means) assert.ok(sec.includes(pct1(s.mean)),label+': '+a.id+' seed '+s.seed);
  }
  for(const m of ['balanced_accuracy','macro_f1']) for(const c of adr.paired_contrasts[m]){
    assert.ok(sec.includes(pp1(c.mean_change)),label+': '+m+' '+c.id+' change');
    assert.ok(sec.includes(ivp(c.bootstrap_95,zh)),label+': '+m+' '+c.id+' interval');
  }
  // The matrix readout sits beside the head-only arm, said to be a different head and not paired.
  assert.ok(sec.includes(matrixLabram.y.toFixed(1)+'%'),label+': the matrix frozen-LaBraM readout is printed for scale');
  assert.match(sec,!zh?/not the best a frozen encoder can do[^.]*not a paired comparison/:/并不是冻结编码器能达到的最好结果[^。]*不是配对比较/,label+': the head-only arm is not the best frozen readout');
  // LoRA vs. last block: an interval across zero is reported as no demonstrated difference.
  const lb=adr.paired_contrasts.balanced_accuracy.find(c=>c.id==='lora-r4_minus_last-block');
  assert.ok(lb.bootstrap_95[0]<0&&lb.bootstrap_95[1]>0);
  assert.match(sec,!zh?/crosses zero, so neither is shown to be better/:/跨过零，所以无法说明哪一个更好/,label+': LoRA vs. last block');
  // Memory was recorded only as lower bounds; none is published. Checked on the
  // whole page now: the adapter's size moved into methods and limits.
  // "RSS" unanchored and in any case (peak RSS, maxrss, max rss): no word on the page contains
  // those letters otherwise, so no exclusion is needed (checked 2026-10-02).
  assert.doesNotMatch(visible(html),/\d\s?(?:MiB|MB|GiB|GB)\b/,label+': no memory figure');
  assert.doesNotMatch(visible(html),/RSS|max ?rss/i,label+': no resident-memory figure or label');
  // The next day: its own section since 2026-10-02, after the adaptation result. No
  // figure anywhere in it — not in the BNCI2015-001 status, not in the cross-session slot.
  const nd=html.slice(html.indexOf('id="next-day"'),html.indexOf('id="methods-and-limits"'));
  assert.ok(html.indexOf('id="next-day"')>html.indexOf('id="adaptation"')&&nd.length>800,label+': the next-day section renders between the adaptation result and methods and limits');
  assert.doesNotMatch(nd,/\d+(?:\.\d+)?\s?%|\d\.\d|pp\b/,label+': the next-day section carries no figure');
  // The two-day experiment: named, its design stated, no figure.
  const next=nd.slice(nd.indexOf('id="two-days"'),nd.indexOf('</p>',nd.indexOf('id="two-days"')));
  assert.ok(nd.indexOf('id="two-days"')>0&&next.length>200,label+': the next-day status renders');
  assert.ok(next.includes(ad.status_only[0].name.split(' · ')[0]),label+': the next-day source is named');
  assert.match(next,!zh?/no figure from it is published/:/不发布它的任何数字/,label+': the next-day status says why');
  // Unlike the adaptation result, the next-day design calibrates on the test person's own labels;
  // the section says so, with the budgets the export states (2026-10-02 review).
  assert.ok(unent(next).includes(zh?'与上面的结果不同，这个设计要用到测试被试本人的标签：用其第一天的试次训练，并且（零预算时除外）用其第二天最前面的试次校准。'
                                  :"Unlike the result above, this design uses the test person's own labels: their day-A trials to train and, except at the zero budget, their first day-B trials to calibrate."),label+': the next-day design uses the test person\'s own day-B labels');
  const budgets=ad.status_only[0].design.calibration_labels;
  assert.ok(next.includes(budgets.slice(0,-1).join(zh?'、':', ')+(zh?' 或 ':' or ')+budgets.at(-1)),label+': the day-B budgets are the export\'s');
  assert.ok(nd.includes(zh?'为它准备了两个数据源；出于不同的原因，两者都不能公开评分。':'Two sources were prepared for it; for different reasons, neither can be scored in public.'),label+': the next-day lede');
  // The hero covers both halves of the page, so it does not carry the adaptation's "zero labels"
  // label over the next-day half; #adaptation, the cards and the snippets keep it.
  const heroEyebrow=(html.match(/<p class="eyebrow">([^<]*)<\/p>\s*<h1>/)||[])[1];
  assert.equal(heroEyebrow,zh?'模型适配 · 新被试；次日实验暂缓发布':'Model adaptation · new people; next day held',label+': the hero eyebrow names both halves of the page');
  assert.doesNotMatch(heroEyebrow,adLabel[label],label+': the hero eyebrow does not put the adaptation label over the next-day half');
  assert.match(sec.match(/<p class="eyebrow">([^<]*)<\/p>/)[1],adLabel[label],label+': the #adaptation eyebrow keeps the label');
  // The cross-session slot: the released status-only entry, named, and why it has no score.
  const cs=nd.slice(nd.indexOf('id="cross-session"'),nd.indexOf('</p>',nd.indexOf('id="cross-session"')));
  assert.ok(nd.indexOf('id="cross-session"')>0&&cs.includes(!zh?cxs.name.split(' · ')[0]:'Stieger 纵向 BCI'),label+': the cross-session source is named');
  assert.match(unent(cs),!zh?/every score would be that person's, so none is published/:/任何分数都是这个人的分数，所以不发布/,label+': the cross-session slot says why it has no score');
  assert.ok(cs.includes(`href="${prefix}/releases/#context-update-20260927"`),label+': the cross-session slot links the release that lists it');
  // No winner, anywhere on the page.
  assert.doesNotMatch(html,!zh?/LoRA (?:is|was) (?:better|best)|outperform/i:/LoRA 更好(?!，)|优于最后/,label+': no winner is declared');
  assert.match(html,/href="\/data\/adaptation-update\.json"/,label+': the reviewed export is linked');
  // The label, wherever the page summarises itself: short answer, meta and share descriptions.
  const ans=unent(html.slice(html.indexOf('<section class="short-answer"'),html.indexOf('</section>',html.indexOf('<section class="short-answer"'))).replace(/<[^>]+>/g,''));
  const meta=k=>unent(html.match(new RegExp(`<meta (?:name|property)="${k}" content="([^"]*)"`))[1]);
  for(const [what,text] of [['short answer',ans],['description',meta('description')],['og:description',meta('og:description')]]){
    assert.match(text,adLabel[label],label+': the '+what+' must say "new people, same task, zero labels from the test person"');
    assert.match(text,nextLabel[label],label+': the '+what+' must call the hold the next day');
  }
  // The short answer gives the three arms and the matrix readout.
  for(const f of [armPct('last-block'),armPct('lora-r4'),armPct('frozen'),matrixLabram.y.toFixed(1)+'%']) assert.ok(ans.includes(f),label+': the short answer gives '+f);
  // The home card.
  const home=pageOf(zh?'zh/':''),at=home.indexOf(`<a class="topic-entry-card" href="${prefix}/topics/model-adaptation/"`);
  const card=home.slice(at,home.indexOf('</a>',at));
  assert.ok(at>0,label+': the home page carries the new card');
  assert.match(card,adLabel[label],label+': the home card names the evidence');
  assert.match(card,nextLabel[label],label+': the home card names the next-day hold');
  // The EEGMAT and LaBraM pages: the group is labelled and sends readers here.
  for(const p of ['datasets/eegmat/','methods/labram/']){
    const e=pageOf((zh?'zh/':'')+p),g0=e.search(/id="g-(?:eegmat-)?eegmat-labram-adaptation"/),g=e.slice(g0,e.indexOf('</p>',g0));
    assert.ok(g0>0&&adLabel[label].test(g),label+'/'+p+': the adaptation group carries the label');
    assert.ok(g.includes(`href="${prefix}/topics/model-adaptation/"`),label+'/'+p+': the adaptation group links its new page');
    assert.ok(!e.includes(`${prefix}/topics/calibration-budget/#adaptation`),label+'/'+p+': nothing still points at the old section');
  }
}
// calibration-budget keeps its question, and the two old anchors as figure-free notes pointing to the new page.
for(const [label,path] of [['en','topics/calibration-budget/'],['zh','zh/topics/calibration-budget/']]){
  const html=pageOf(path),zh=label==='zh',prefix=zh?'/zh':'';
  for(const id of ['adaptation','next-day']){
    const at=html.indexOf(`id="${id}"`),note=html.slice(at,html.indexOf('</section>',at));
    assert.ok(at>0,label+': #'+id+' must stay, so old links keep working');
    assert.ok(note.includes(`href="${prefix}/topics/model-adaptation/#${id}"`),label+': #'+id+' sends readers to the new page');
    assert.doesNotMatch(note.replace(/<[^>]+>/g,' '),/\d/,label+': the #'+id+' note carries no figure');
    assert.ok(note.length<1200,label+': #'+id+' is a note, not the moved section');
  }
  // A link to #next-day lands on its own heading, so the heading cannot lean on the one above it.
  const ndH2=(html.match(/id="next-day"[^>]*>\s*<h2[^>]*>([^<]*)<\/h2>/)||[])[1];
  assert.equal(ndH2,zh?'次日实验已移到模型适配页面':'The next-day experiment has moved to the model-adaptation page',label+': the #next-day heading stands on its own');
  assert.match(html.slice(html.indexOf('id="adaptation"')),adLabel[label],label+': the note says what the moved evidence is');
  // None of the moved figures, and not its export, remain.
  for(const a of adr.arms) assert.ok(!html.includes(pct1(a.balanced_accuracy.mean)),label+': '+a.id+' moved off this page');
  for(const c of adr.paired_contrasts.balanced_accuracy) assert.ok(!html.includes(pp1(c.mean_change)),label+': '+c.id+' moved off this page');
  assert.doesNotMatch(html,/href="\/data\/adaptation-update\.json"/,label+': the adaptation export is cited where its figures are');
  assert.doesNotMatch(html,!zh?/LoRA (?:is|was) (?:better|best)|outperform/i:/LoRA 更好(?!，)|优于最后/,label+': no winner is declared');
  // The eTRCA filter-bank wording, corrected; and the short answer says the eTRCA is single-band (content audit #5).
  assert.doesNotMatch(html,/three-filter-bank|三子带/,label+': the corrected eTRCA wording');
  const ans=unent(html.slice(html.indexOf('<section class="short-answer"'),html.indexOf('</section>',html.indexOf('<section class="short-answer"'))));
  assert.match(ans,!zh?/one fixed band, not the original method's filter bank/:/只用一个固定频带，而不是原方法的滤波器组/,label+': the single-band eTRCA caveat travels with the short answer');
}
// The holds register sends the next-day hold to the new page's section, and every hold link lands on an anchor that exists.
for(const [label,path] of [['en','releases/'],['zh','zh/releases/']]){
  const html=pageOf(path),reg=html.slice(html.indexOf('id="holds"'),html.indexOf('</table>',html.indexOf('id="holds"')));
  const prefix=label==='zh'?'/zh':'';
  assert.match(reg,new RegExp(`href="${prefix}/topics/model-adaptation/#next-day">[^<]*${label==='zh'?'次日':'next-day'}`),label+': the next-day hold links its section');
  for(const [,href,page,id] of reg.matchAll(/href="((\/[^"#]*)#([^"]+))"/g)){
    if(page==='/'+(label==='zh'?'zh/':'')+'releases/') continue;
    assert.ok(pageOf(page.slice(1)).includes(`id="${id}"`),label+': hold link '+href+' lands on no anchor');
  }
}
// The entity pages carry the new rows, re-read from their file by the entity checks above.
for(const p of ['datasets/eegmat/','zh/datasets/eegmat/','methods/labram/','zh/methods/labram/'])
  assert.ok(pageOf(p).includes('adaptation-update.json|'),p+': adaptation figures must reach the entity page');
// Releases: the batch, its manifest hash, and the corrections register.
for(const [label,path] of [['en','releases/'],['zh','zh/releases/']]){
  const html=pageOf(path);
  assert.ok(html.includes(`id="${ad.release_id}"`)&&html.includes(ad.provenance.manifest_sha256),label+': the adaptation release and its manifest');
  const corr=html.slice(html.indexOf('id="corrections"'),html.indexOf('id="holds"'));
  assert.equal((corr.match(/<tr>/g)||[]).length-1,2,label+': two corrections listed');
  assert.match(corr,/heliyon|Heliyon/,label+': the ds003810 citation correction');
}
// ds003810: the citation its OpenNeuro record asks for, on both dataset pages.
for(const p of ['datasets/ds003810/','zh/datasets/ds003810/'])
  assert.ok(pageOf(p).includes('https://doi.org/10.1016/j.heliyon.2020.e03425'),p+': the requested citation');
// The released evidence policy (mvp.json) under 'How these results were produced': printed as released on /,
// and on /zh/ translated, with the released English verbatim beside it (2026-10-06).
{
  const esc=t=>t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const sec=p=>{const h=pageOf(p);const i=h.indexOf('id="methods"');assert.ok(i>=0,p+': #methods');return h.slice(i,h.indexOf('</section>',i));};
  const en=sec(''), zh=sec('zh/'), policy=esc(data.evidencePolicy);
  assert.ok(en.includes('<p>'+policy+'</p>'),'/: the released evidence policy, as released');
  assert.ok(!/note-original/.test(en),'/: no translation note on the English page');
  assert.ok(zh.includes('<p>只导出经过明确审核的队列层面研究结果。原始 EEG、个人结果和模型权重都不放到网站上。每项比较都写明来源、许可、协议和局限。没有跨任务的总分。</p>'),'/zh/: the evidence policy in Chinese');
  assert.ok(zh.includes('<p class="note-original" lang="en">'+policy+'</p>'),'/zh/: the released English beside the translation, verbatim');
  assert.ok(zh.indexOf('只导出经过明确审核')<zh.indexOf('note-original'),'/zh/: the translation comes first');
}
// The API page's Python example: since 2026-10-05 the CDN lets any client read /data/
// (a Cloudflare configuration rule turns the browser check off there), so pandas reads
// the CSV from its URL, and the page no longer tells readers urllib is refused.
for(const p of ['api/','zh/api/']){
  const html=pageOf(p);
  assert.match(html,/pd\.read_csv\((?:&quot;|")https:\/\/bci\.report\/data\/mi-rest-results\.csv(?:&quot;|")\)/,p+': pandas reads the CSV from its /data/ URL');
  assert.doesNotMatch(html,/io\.StringIO|refuses Python|会拒绝 Python/,p+': no workaround for a refusal that no longer applies');
}
// The "Research preview" badge is gone from every page and agent file (2026-10-01).
// The core release keeps its id, research-preview-20260920, which is a label for bytes.
{
  const walk=d=>readdirSync(new URL(d,DIST),{withFileTypes:true}).flatMap(e=>e.isDirectory()?(e.name==='data'||e.name==='_astro'?[]:walk(d+e.name+'/')):[d+e.name]);
  for(const f of walk('').filter(f=>/\.(html|md|txt)$/.test(f)))
    assert.doesNotMatch(readFileSync(new URL(f,DIST),'utf8'),/Research preview|research preview|研究预览/,f+': the stage label must not return');
}

// CITATION.cff names the newest release on the releases page.
const newest=pageOf('releases/').match(/<article class="release-entry" id="([^"]+)"/)[1];
assert.match(readFileSync(new URL('../../CITATION.cff',import.meta.url),'utf8'),new RegExp('^version: "'+newest+'"$','m'),'CITATION.cff must cite the newest release, '+newest);
// IndexNow: the key file ships and holds exactly its own name.
const keyFile=distFiles.find(f=>/^[0-9a-f]{32}\.txt$/.test(f));
assert.ok(keyFile&&readFileSync(new URL(keyFile,DIST),'utf8').trim()===keyFile.slice(0,-4),'IndexNow key file must ship and contain its own name');
// A held source is named on no page, in no Markdown copy and in no agent file.
for(const h of held) for(const f of distFiles.filter(f=>/\.(?:html|md|txt)$/.test(f))){
  const text=readFileSync(new URL(f,DIST),'utf8');
  assert.ok(!text.includes(h.name)&&!text.includes(h.source.split('/').pop()),f+': held source '+h.id+' appears');
}

// --- 2026-10-02 extension batch: YSU twenty-person extension, LTRSVP -----------
const xt=JSON.parse(readFileSync(new URL('../src/data/extension-update.json',import.meta.url),'utf8'));
assert.deepEqual(Object.keys(xt.results).sort(),['ltrsvp-rate-transfer','ysu-async-ssvep-extension'],'only the two reviewed v7 sources carry numbers');
assert.deepEqual(xt.status_only,[],'this batch has no status-only source');
assert.deepEqual(
  readFileSync(new URL('../src/data/extension-update.json',import.meta.url)),
  readFileSync(new URL('../public/data/extension-update.json',import.meta.url)),
  'source and downloadable extension exports must be byte-identical',
);
const yx=xt.results['ysu-async-ssvep-extension'], lx=xt.results['ltrsvp-rate-transfer'];
const [gR,pR]=yx.rules, yd=yx.paired_difference, ld=lx.paired_difference;
const frac=(k,n)=>`${k} / ${n}`, ratio=(k,n)=>pct1(k/n);
const signed3=v=>(v>=0?'+':'−')+Math.abs(v).toFixed(3);
const tcInterval={en:'95% interval',zh:'95% 区间'};
// The handoffs' headline figures, so a changed export cannot pass by changing the page with it.
assert.deepEqual([gR.id,pR.id],['global','personal']);
assert.deepEqual(yx.rules.map(r=>pct1(r.detection_balanced_accuracy.mean)),['76.0%','79.0%'],'detection balanced accuracy, both rules');
assert.deepEqual(yx.rules.map(r=>frac(r.non_control_pooled.accepted,r.non_control_pooled.tested)),['249 / 960','190 / 960'],'pooled non-control false acceptance, both rules');
assert.deepEqual([pp1(yd.mean),ivp(yd.bootstrap_95,false)],['+3.0 pp','+0.5 to +5.7 pp'],'the paired YSU difference');
assert.deepEqual([yd.helped,yd.harmed,yd.tied],[10,8,2],'people helped, harmed and tied');
assert.equal(yd.helped+yd.harmed+yd.tied,yx.cohort.people,'helped + harmed + tied is the cohort');
assert.ok(pR.control_windows.accepted_and_correct<=gR.control_windows.accepted_and_correct,'the trade-off wording needs end-to-end output not to rise');
assert.deepEqual(lx.primary.arms.map(a=>pct1(a.balanced_accuracy.mean)),['60.8%','63.0%'],'the two LTRSVP primary arms');
assert.deepEqual([pp1(ld.mean),ivp(ld.bootstrap_95,false)],['−2.2 pp','−6.8 to +2.8 pp'],'the paired LTRSVP difference');
assert.ok(ld.bootstrap_95[0]<0&&ld.bootstrap_95[1]>0&&ld.interval_crosses_zero===true,'the rate interval crosses zero');
assert.deepEqual([ld.people_lower,ld.people_higher,ld.people_tied],[7,2,0]);
assert.equal(ld.people_lower+ld.people_higher+ld.people_tied,lx.cohort.people,'lower + higher + tied is the cohort');
assert.equal(lx.not_causal,true);
// Wording that would overclaim: a negation must stand within the preceding 40 characters.
const negated=(html,re,label,neg=/\bnot\b|\bno\b|n’t|没有|并非|不是|不能|不等于/)=>{
  for(const m of html.matchAll(re)) assert.match(html.slice(Math.max(0,m.index-40),m.index),neg,label+': "'+m[0]+'" reads as a claim');
};
const perHour=/\d+(?:\.\d+)?\s*%?\s*(?:false (?:activations?|acceptances?)\s*)?(?:per hour|an hour|\/\s*h(?:our)?\b)|每小时\s*\d|\d+(?:\.\d+)?\s*次\s*\/\s*小时/;
for(const [label,path] of [['en','topics/when-not-to-act/'],['zh','zh/topics/when-not-to-act/']]){
  const zh=label==='zh', html=pageOf(path);
  const sec=html.slice(html.indexOf('id="non-control"'),html.indexOf('id="methods-and-limits"'));
  const pilotAt=sec.indexOf('id="non-control-pilot"');
  assert.ok(pilotAt>3000,label+': the twenty-person extension leads the section and the pilot follows it');
  const ext=sec.slice(0,pilotAt);
  // Both rules, every measure: detection with its interval, coverage, end to end, conditional accuracy.
  // Table cells, matched as cells: the same counts also appear in the prose around the table.
  const cell=(k,n)=>'<span class="metric">'+frac(k,n)+'</span><span class="interval">'+ratio(k,n)+'<';
  for(const r of yx.rules){
    const w=r.control_windows, ba=r.detection_balanced_accuracy;
    for(const v of ['<span class="metric">'+pct1(ba.mean)+'</span><span class="interval">'+tcInterval[label]+' '+pct1(ba.bootstrap_95[0])+'–'+pct1(ba.bootstrap_95[1])+'<',
                    cell(w.accepted,w.tested),cell(w.accepted_and_correct,w.tested),
                    '<span class="metric">'+pct1(r.accepted_window_accuracy_mean_over_people)+'</span>'])
      assert.ok(ext.includes(v),label+': '+r.id+' rule figure '+v);
    // Conditional accuracy never before coverage and the end-to-end rate.
    const acc=ext.indexOf('<span class="metric">'+pct1(r.accepted_window_accuracy_mean_over_people)+'</span>');
    const cov=ext.indexOf(cell(w.accepted,w.tested)), e2e=ext.indexOf(cell(w.accepted_and_correct,w.tested));
    assert.ok(cov>0&&e2e>0&&acc>cov&&acc>e2e,label+': '+r.id+' coverage and end-to-end rate come before conditional accuracy');
    // Per-state false acceptance, as counts and rates.
    for(const f of r.false_acceptance)
      assert.ok(ext.includes(cell(f.accepted,f.tested)),label+': '+r.id+' '+f.state+' false acceptance');
    // The pooled row (2026-10-02 review): the overall count the short answer's "fewer non-control
    // windows overall" reads, from the export, after the states it sums.
    const pooled=r.non_control_pooled;
    assert.equal(pooled.accepted,r.false_acceptance.reduce((a,f)=>a+f.accepted,0),r.id+': the pooled count is the sum of the states');
    assert.equal(pooled.tested,r.false_acceptance.reduce((a,f)=>a+f.tested,0),r.id+': the pooled windows are the sum of the states');
    const pr=ext.indexOf('<tr class="pooled-row">'),pooledRow=pr<0?'':ext.slice(pr,ext.indexOf('</tr>',pr));
    assert.ok(pooledRow.includes(zh?'三种状态合并':'All three states, pooled')&&pooledRow.includes(cell(pooled.accepted,pooled.tested)),label+': '+r.id+' pooled non-control row');
    for(const f of r.false_acceptance) assert.ok(ext.indexOf(cell(f.accepted,f.tested))<pr,label+': '+r.id+' '+f.state+' comes before the pooled row');
  }
  // The three states are named and described, not only coded.
  for(const [st,en,cn] of [['NS1','Central image, flicker off','注视中央图像，闪烁关闭'],['NS2','Looking at a white wall, resting','看着白墙休息'],['NS3','Central image while the surrounding targets flicker','注视中央，周围目标在闪烁']])
    assert.ok(ext.includes('>'+st+'<')&&ext.includes(zh?cn:en),label+': state '+st+' is described');
  // The paired difference with its interval, and the people behind the mean.
  assert.ok(ext.includes('<strong>'+pp1(yd.mean)+'</strong>')&&ext.includes(ivp(yd.bootstrap_95,zh)),label+': the paired difference and its interval');
  assert.ok(ext.includes(zh?`${yx.cohort.people} 名被试中 ${yd.helped} 人提升、${yd.harmed} 人变差、${yd.tied} 人不变`
                           :`${yd.helped} of ${yx.cohort.people} people improved, ${yd.harmed} got worse and ${yd.tied} were unchanged`),label+': helped, harmed and tied are visible');
  // The trade-off, in words: detection up, correct-and-accepted not up.
  assert.match(ext,zh?/检测上升了，正确的指令并没有增加。/:/Detection went up; correct commands did not\./,label+': the trade-off is stated');
  negated(html,zh?/更高的指令准确率|指令准确率更高|更多正确的指令|提高了指令准确率/g:/better command accuracy|more correct commands|improv\w* command accuracy|higher command accuracy/gi,label);
  // The limits of the extension.
  const lim=ext.slice(ext.indexOf('id="non-control-limits"'));
  for(const re of zh?[/同一份数据、同一实验室、同一协议/,/不是来自独立队列的证据/,new RegExp(pR.target_person_labels+' 个带标签的窗口'),/不是连续使用中每小时的误触发次数/,/没有说明 EEG 数值的物理单位/,/本身无单位/]
                    :[/same release, lab and protocol as the pilot/,/not evidence from an independent cohort/,new RegExp(pR.target_person_labels+' labelled windows'),/not false activations per hour/,/no physical unit/,/unit-free/])
    assert.match(lim,re,label+': extension limit '+re);
  assert.doesNotMatch(visible(html),perHour,label+': no per-hour rate is claimed');
  // Credits, and the extension's own download.
  assert.match(ext+sec.slice(pilotAt),/10\.1080\/27706710\.2024\.2418650/,label+': the data paper is credited');
  assert.match(sec,/10\.6084\/m9\.figshare\.24906300\.v3/,label+': the versioned release is credited');
  assert.match(sec,/href="\/data\/extension-update\.json"/,label+': the reviewed extension export is linked');
  // The short answer cites the extension under the rule fixed on the pilot, not the pilot itself.
  const ans=html.slice(html.indexOf('<section class="short-answer"'),html.indexOf('</section>',html.indexOf('<section class="short-answer"')));
  assert.ok(ans.includes('>'+frac(gR.control_windows.accepted,gR.control_windows.tested)+'<'),label+': the short answer cites the extension');
  assert.ok(!ans.includes('130 / 192'),label+': the short answer no longer leads with the pilot');
  // The personal-threshold sentence is qualified: 96 of the person's own labelled windows, fewer
  // false acceptances overall and in each state, no more correct output, and personalisation not
  // separable from having the labels. Its figure is in the evidence (the short-answer check).
  assert.ok(ans.includes('class="fig">'+pR.target_person_labels+'<'),label+': the short answer names the '+pR.target_person_labels+' labelled windows');
  assert.ok(visible(ans).includes(zh?'被误接受的非控制窗口总体减少，每种状态下也都减少了，但被接受且正确的指令占比并没有提高；这项对比无法区分“按人拟合阈值”和“仅仅多了这些标签”各自的作用。'
                               :'accepted fewer non-control windows overall, and fewer in each state, but did not raise the share of commands both accepted and correct; the contrast cannot separate fitting the threshold to the person from simply having those labels.'),label+': the personal-threshold sentence is qualified');
  assert.doesNotMatch(ans,/fitting the threshold to each person cut those mistakes|改为按每名被试拟合阈值后，这类误接受减少了/,label+': the unqualified sentence');
  // ...and held to the numbers it summarises.
  assert.ok(pR.non_control_pooled.accepted<gR.non_control_pooled.accepted&&pR.false_acceptance.every((s,i)=>s.accepted<gR.false_acceptance[i].accepted),'the answer says fewer overall and in each state');
  assert.ok(pR.control_windows.accepted_and_correct<=gR.control_windows.accepted_and_correct,'the answer says correct output did not rise');
  // The eyebrow: the rules were fixed before scoring; only the global threshold came from the pilot.
  assert.ok(sec.includes(zh?`规则在评分前固定；全局阈值来自 ${yx.development_pilot.people} 人试点`:`rules fixed before scoring; global threshold from a ${yx.development_pilot.people}-person pilot`),label+': the eyebrow');
  assert.doesNotMatch(sec,/rules fixed on a \d+-person pilot|规则在 \d+ 人试点上固定/,label+': the personal rule was not fixed on the pilot');
  // The held-out windows the lede counts are the test partition. Calibration and test are both
  // 96 windows a person here, so the page cannot tell the fields apart; the source can.
  const wntaSource=readFileSync(new URL('../src/pages/[...lang]/topics/when-not-to-act.astro',import.meta.url),'utf8');
  for(const lede of wntaSource.match(/^ {4}ncLede: .*$/gm)??[])
    assert.ok(lede.includes('${testWindowsEach}')&&!lede.includes('calibration_windows_each_person'),'when-not-to-act.astro: the lede counts held-out windows from test_windows_each_person');
  assert.equal((wntaSource.match(/^ {4}ncLede: .*$/gm)??[]).length,2,'when-not-to-act.astro: one lede per language');
  const testEach=Object.values(yx.cohort.test_windows_each_person).reduce((a,b)=>a+b,0);
  assert.ok(sec.includes(zh?`两种规则在每名被试相同的 ${testEach} 个留出窗口上评分`:`Both rules score the same ${testEach} held-out windows of each person`),label+': the held-out count');
  // Four scrolling tables, each named for what it holds (a screen reader lists regions by name).
  const regions=[...sec.matchAll(/role="region" aria-label="([^"]+)"/g)].map(m=>m[1]);
  assert.equal(regions.length,4,label+': four table regions in the non-control section');
  assert.equal(new Set(regions).size,4,label+': each table region has its own name');
  regions.forEach((name,i)=>assert.match(name,(zh?[/^扩展：.*指令窗口/,/^扩展：.*非控制状态/,/^试点：指令窗口/,/^试点：非控制状态/]:[/^Extension, command windows/,/^Extension, non-control states/,/^Pilot, command windows/,/^Pilot, non-control states/])[i],label+': region '+i+' is "'+name+'"'));
  // The roadmap names its inputs without a figure (the figure check above covers it); it calls the pilot a development set.
  const road=html.slice(html.indexOf('id="decision-research"'),html.indexOf('class="topic-switcher"'));
  const note=road.slice(road.indexOf(zh?'第一个带有明确非控制状态的输入':'The first input with explicit non-control states'));
  assert.ok(note.length>40,label+': the roadmap inputs note renders');
  assert.match(note.slice(0,note.indexOf('</p>')),zh?/开发集/:/development set/,label+': the roadmap describes the pilot as the development set');
  assert.doesNotMatch(note.slice(0,note.indexOf('</p>')),/\d/,label+': the roadmap inputs note names its inputs without a single figure');
}
for(const [label,path] of [['en','topics/screen-to-vr/'],['zh','zh/topics/screen-to-vr/']]){
  const zh=label==='zh', html=pageOf(path);
  const sec=html.slice(html.indexOf('id="image-rate"'),html.indexOf('id="methods-and-limits"'));
  assert.ok(sec.length>3000,label+': the image-rate section renders before methods and limits');
  for(const a of lx.primary.arms){
    assert.ok(sec.includes('<div class="reading">'+pct1(a.balanced_accuracy.mean)+'</div>'),label+': '+a.id+' score on its card');
    assert.ok(sec.includes(pct1(a.balanced_accuracy.bootstrap_95[0])+'–'+pct1(a.balanced_accuracy.bootstrap_95[1])),label+': '+a.id+' interval');
    assert.ok(sec.includes(a.auroc.mean.toFixed(3)),label+': '+a.id+' AUROC');
  }
  assert.ok(sec.includes('<strong>'+pp1(ld.mean)+'</strong>')&&sec.includes(ivp(ld.bootstrap_95,zh)),label+': the paired difference and its interval');
  // The matrix note says what the diagonal is: run b at the same rate, after a long break — not
  // "only the recording changes" (2026-10-02 review).
  assert.ok(sec.includes(zh?'对角线上，测试记录是同一速率的 b 段，隔了较长的休息才记录；对角线以外，速率也变了，两段记录在实验中相隔多远也随之不同。'
                           :'On the diagonal the test recording is the same-rate run b, after a long break; off it, the rate also changes, and so does how far apart in the session the two recordings were.'),label+': the matrix note on the diagonal');
  assert.doesNotMatch(sec,/On the diagonal only the recording changes|对角线上只换了记录/,label+': the old diagonal wording');
  assert.match(sec,zh?/跨过零，所以不能认定有变化/:/it crosses zero, so no change is established/,label+': the interval-crosses-zero wording');
  assert.ok(sec.includes(zh?`${lx.cohort.people} 名被试中 ${ld.people_lower} 人的点估计更低、${ld.people_higher} 人更高`
                           :`${ld.people_lower} of ${lx.cohort.people} people had a lower point estimate and ${ld.people_higher} a higher one`),label+': lower and higher counts are visible');
  assert.ok(sec.includes(signed3(lx.secondary_auroc_difference.mean)),label+': the AUROC contrast travels with it');
  // The full 3×3 matrix, every cell with its interval, nothing else in that table.
  const table=sec.slice(sec.indexOf('<table>'),sec.indexOf('</table>'));
  assert.equal((table.match(/class="metric"/g)||[]).length,9,label+': the matrix has nine cells');
  for(const m of lx.matrix)
    assert.ok(table.includes('>'+pct1(m.balanced_accuracy.mean)+'</span><span class="interval">'+pct1(m.balanced_accuracy.bootstrap_95[0])+'–'+pct1(m.balanced_accuracy.bootstrap_95[1])+'<'),label+': matrix cell '+m.train_rate_hz+'→'+m.test_rate_hz);
  // Rate and recording are confounded; nothing is called causal unless negated.
  const lim=sec.slice(sec.indexOf('id="image-rate-limits"'));
  assert.match(lim,zh?/速率与记录相互混杂/:/Rate and recording are confounded/,label+': the confound is a stated limit');
  assert.match(lim,zh?/不是图像速率的因果效应/:/not a causal effect of image rate/,label+': not causal');
  negated(html,zh?/因果/g:/causal|causes|caused by (?:the )?(?:image )?rate/gi,label);
  assert.doesNotMatch(visible(html),/(?:image|presentation|faster|slower) rate (?:reduces|lowers|degrades|harms|improves|raises)|速率(?:导致|造成|降低了|提高了)/i,label+': no rate effect is claimed');
  assert.doesNotMatch(visible(html),perHour,label+': no per-hour rate is claimed');
  // Credits: the PhysioNet record, the original publication, the licence, the ethics committee.
  for(const re of [/10\.13026\/C2KX0P/,/10\.1371\/journal\.pone\.0178498/,/Riccardo Poli/,/opendatacommons\.org\/licenses\/by\/1-0/,
                   zh?/埃塞克斯大学（University of Essex）伦理委员会批准/:/approved by the Ethics Committee of the University of Essex/])
    assert.match(sec,re,label+': LTRSVP credit '+re);
  assert.match(sec,/href="\/data\/extension-update\.json"/,label+': the reviewed extension export is linked');
  // Presentation order: what the original publication reports, what PhysioNet does not
  // document, and what follows for a cross-rate cell (2026-10-02 review; quotes in the manifest).
  assert.match(lim,zh?/各速率按从低到高的顺序呈现，而且这一顺序没有在被试之间随机化/:/presented from the lowest to the highest, in an order not randomised across participants/,label+': the known order');
  assert.match(lim,zh?/PhysioNet 没有说明/:/not documented on PhysioNet/,label+': what is not documented');
  assert.match(lim,zh?/经过的时间、疲劳和练习程度也不同/:/also differs in elapsed time, fatigue and practice/,label+': what the order adds to a cross-rate cell');
  assert.doesNotMatch(sec,/Order across rates unknown|order between rates is not established|速率之间的先后未知|先后没有确定/,label+': the order is partly known; say what is');
}
assert.ok(/lowest to the highest/.test(lx.presentation_order.known)&&/not randomised/.test(lx.presentation_order.known)&&lx.presentation_order.sources.includes('https://doi.org/10.1371/journal.pone.0178498'),'the export records the known order and its source');
// "Later recording" (之后的记录, 之后一段) only where it is true: within a rate, run b followed
// run a after a long break. Across rates the study's order was ascending and how the released
// files map onto it is not documented, so a cross-rate test recording is a different one, not
// a later one. Every page, Markdown copy, agent file, the feed and the export.
{
  const laterRe=/\blater\b[^.;:。；]{0,40}\brecording|之后的记录|之后一段/g, withinRate=/[Ww]ithin (?:a|each|one) rate|同一速率内/;
  const ends=['. ','; ','。','；'];
  const sentenceAt=(text,i)=>{const b=Math.max(...ends.map(s=>{const k=text.lastIndexOf(s,i);return k<0?-1:k+s.length;}),0);
    const e=Math.min(...ends.map(s=>{const k=text.indexOf(s,i);return k<0?text.length:k;}));return text.slice(b,e);};
  const laterOnlyWithinRate=(text,where)=>{for(const m of text.matchAll(laterRe))
    assert.match(sentenceAt(text,m.index),withinRate,where+': "'+m[0]+'" outside a within-rate sentence: '+sentenceAt(text,m.index).slice(0,160));};
  let seen=0;
  for(const f of [...distFiles.filter(f=>/\.(?:html|md|txt|xml)$/.test(f))]){
    const raw=readFileSync(new URL(f,DIST),'utf8'),text=f.endsWith('.html')?visible(raw):raw.replace(/\s+/g,' ');
    laterOnlyWithinRate(text,f);seen+=(text.match(laterRe)||[]).length;
  }
  laterOnlyWithinRate(JSON.stringify(xt).replace(/\\"/g,'"'),'extension-update.json');
  assert.ok(seen>=4,'the within-rate sentence itself renders (screen-to-vr, both languages, and their Markdown copies)');
}
// The dataset pages print the reading beside each paired row, as the topic pages do: how many
// people moved which way (counts re-read from the export), and for LTRSVP that the interval
// crosses zero and that rate and recording are confounded.
for(const [label,p,d,counts,reading] of [
  ['en','datasets/ltrsvp/',ld,[ld.people_lower,ld.people_higher],/people lower, <span[^>]*>2<\/span> higher\. The interval crosses zero: no change is established\. Rate and recording change together: not a causal effect of image rate\./],
  ['zh','zh/datasets/ltrsvp/',ld,[ld.people_lower,ld.people_higher],/人更低、<span[^>]*>2<\/span> 人更高。区间跨过零，不能认定有变化。速率与记录一起变化：不是图像速率的因果效应。/],
  ['en','datasets/ysu-async-ssvep/',yd,[yd.helped,yd.harmed,yd.tied],/people improved, <span[^>]*>8<\/span> got worse, <span[^>]*>2<\/span> unchanged/],
  ['zh','zh/datasets/ysu-async-ssvep/',yd,[yd.helped,yd.harmed,yd.tied],/人提升、<span[^>]*>8<\/span> 人变差、<span[^>]*>2<\/span> 人不变/]]){
  const html=pageOf(p),at=html.indexOf(`data-fig="extension-update.json|pp1|${d.mean}"`),end=html.indexOf('</tr>',at);
  const n0=html.indexOf('class="row-note"',at),note=n0>0&&n0<end?html.slice(n0,end):'';
  assert.ok(at>0&&note,p+': the paired row carries its reading');
  assert.deepEqual([...note.matchAll(/data-fig="extension-update\.json\|count\|(\d+)"/g)].map(m=>Number(m[1])),counts,p+': the people behind the paired mean, in order');
  assert.match(note,reading,p+': the reading beside the paired row');
}
for(const [p,title] of [['datasets/ltrsvp/','Image rate · trained on one recording at one rate, tested on a different recording'],['zh/datasets/ltrsvp/','图像速率 · 在一种速率的一段记录上训练、在另一段记录上测试']])
  assert.ok(pageOf(p).includes(title),p+': the group title calls the test recording different, not later');
// Dataset pages: the YSU page gains the extension group; LTRSVP has its own page. Their figures
// are re-read from the served file by the entity checks above.
for(const p of ['datasets/ysu-async-ssvep/','zh/datasets/ysu-async-ssvep/','datasets/ltrsvp/','zh/datasets/ltrsvp/'])
  assert.ok(pageOf(p).includes('data-fig="extension-update.json|'),p+': extension figures must reach the dataset page');
assert.ok(pageOf('datasets/ltrsvp/').includes('10.1371/journal.pone.0178498')&&pageOf('datasets/ltrsvp/').includes('Open Data Commons Attribution License 1.0'),'LTRSVP dataset page: credit and licence');
assert.equal((pageOf('datasets/ltrsvp/').match(/data-fig="extension-update\.json\|pct1\|/g)||[]).length,9*3+1,'LTRSVP dataset page: nine cells with intervals, and the chance level');
// Releases: the batch and its manifest hash.
for(const [label,path] of [['en','releases/'],['zh','zh/releases/']]){
  const html=pageOf(path);
  assert.ok(html.includes(`id="${xt.release_id}"`)&&html.includes(xt.provenance.manifest_sha256),label+': the extension release and its manifest');
}
assert.ok(llms.includes('https://bci.report/datasets/ltrsvp/index.md'),'llms.txt: the LTRSVP dataset page');
console.log('PASS: 2026-10-02 extension — both rejection rules side by side with coverage, end-to-end rate and per-state false acceptance; helped/harmed shown; trade-off and limits stated; LTRSVP arms, crossing interval and full matrix; no causal, per-hour or command-accuracy claim; presentation order stated and "later recording" only within a rate; YSU answer qualified, eyebrow, test-window count and four named table regions; credits; dataset pages with the people behind each paired mean.');

// --- 2026-10-03 large-source batch: Dreem sleep staging, OpenBMI next session -----------
// Two questions, each with two fixed classical baselines and nothing shared between them.
// Dreem has its own topic (sleep-staging, owner decision); OpenBMI broadened calibration-budget
// (#next-session). Every figure on the new sections is printed with data-fig and re-read from
// large-source-update.json above (the topic data-fig loop); what is pinned here is what must
// travel with those figures and what must never be said.
{
  const ls=JSON.parse(readFileSync(new URL('../src/data/large-source-update.json',import.meta.url),'utf8'));
  assert.deepEqual(Object.keys(ls.results).sort(),['dreem-sleep-baselines','openbmi-cross-session-calibration'],'only the two reviewed sources carry numbers');
  assert.deepEqual(ls.status_only,[],'this batch has no status-only source');
  assert.deepEqual(ls.holds.map(h=>h.id),['dreem-amplitude-sensitive-models'],'one hold, figure-free');
  assert.deepEqual(readFileSync(new URL('../src/data/large-source-update.json',import.meta.url)),readFileSync(new URL('../public/data/large-source-update.json',import.meta.url)),
    'source and downloadable large-source exports must be byte-identical');
  const dr=ls.results['dreem-sleep-baselines'],ob=ls.results['openbmi-cross-session-calibration'];
  const coh=['DOD-H','DOD-O'],C=Object.fromEntries(coh.map(c=>[c,dr.cohorts[c]]));
  const arms=['training_prior','spectral_ridge'];
  // The handoffs' headline figures, so a changed export cannot pass by changing the page with it.
  assert.deepEqual(coh.map(c=>{const k=C[c],a=k.arms;return [k.nights,pct1(a.spectral_ridge.accuracy.mean),pct1(a.spectral_ridge.balanced_accuracy.mean),
    pct1(a.training_prior.accuracy.mean),pct1(a.training_prior.balanced_accuracy.mean),pp1(k.paired_balanced_accuracy.mean),ivp(k.paired_balanced_accuracy.interval_95,false)];}),
    [[25,'72.3%','56.7%','48.0%','20.2%','+36.5 pp','+32.9 to +39.8 pp'],[55,'72.5%','49.3%','49.2%','20.5%','+28.8 pp','+26.7 to +30.7 pp']],'the Dreem handoff figures');
  const ra=dr.record_accounting,ea=dr.epoch_accounting;
  assert.equal(ra.archive_records-ra.excluded_before_scoring,ra.evaluated,'81 - 1 = 80 records');
  assert.equal(ra.evaluated,C['DOD-H'].nights+C['DOD-O'].nights,'80 = 25 + 55');
  assert.equal(ea.total-ea.unscored-ea.zero_or_invalid_channel_scale,ea.eligible,'77,901 - 3 - 75 = 77,823 epochs');
  assert.equal(ea.eligible,C['DOD-H'].eligible_epochs+C['DOD-O'].eligible_epochs,'the eligible epochs are the two cohorts\' own');
  const gain=(a,t)=>a.calibration_gain.find(g=>g.target_trials===t);
  const [lc,psd]=ob.arms,lc40=gain(lc,40),psd40=gain(psd,40);
  assert.equal(ob.cohort.acquisition_identities,ob.cohort.engineering_exclusion+ob.cohort.input_quality_holds+ob.cohort.evaluated,'54 = 1 + 2 + 51');
  assert.equal(ob.cohort.unique_test_trials,ob.cohort.evaluated*ob.cohort.test_trials_each_person,'3,060 = 51 x 60');
  assert.equal(ob.cohort.jobs.trained,ob.cohort.evaluated*ob.arms.length*ob.protocol.session_2_budgets.length,'408 = 51 x 2 x 4');
  assert.deepEqual(ob.protocol.session_2_budgets,[0,10,20,40]);
  assert.deepEqual([pp1(lc40.balanced_accuracy_change.mean),ivp(lc40.balanced_accuracy_change.interval_95,false),lc40.people_with_any_decline,lc40.people_with_decline_of_5_points_or_more,lc40.interval_excludes_zero],
    ['+4.6 pp','+2.3 to +6.9 pp',13,6,true],'the log-covariance 40-versus-0 figures');
  assert.deepEqual([pp1(psd40.balanced_accuracy_change.mean),ivp(psd40.balanced_accuracy_change.interval_95,false),psd40.people_with_any_decline,psd40.people_with_decline_of_5_points_or_more,psd40.interval_excludes_zero],
    ['+1.7 pp','−0.1 to +3.5 pp',16,6,false],'the relative-PSD 40-versus-0 figures');

  // Every figure-like token a section prints — one-decimal percentages, pp, kappas, grouped
  // counts — is a value of its source, formatted as the site formats it, or a number written in
  // the source's own text (a DOI, "0.5–30 Hz"). A typed figure, or one from the unpublished
  // 40-person OpenBMI snapshot, has nothing to match.
  const tokensOf=obj=>{const out=new Set();const walk=v=>{if(typeof v==='number'){for(const g of fmtEarlier)for(const n of numbers(g(v)))out.add(n);}
    else if(typeof v==='string'){for(const n of numbers(v))out.add(n);}else if(v&&typeof v==='object')Object.values(v).forEach(walk);};walk(obj);return out;};
  const figureLike=t=>[...t.matchAll(/\d+\.\d+|\d{1,3}(?:,\d{3})+/g)].map(m=>m[0]);
  const drTokens=tokensOf(dr),obTokens=tokensOf(ob);
  const ldIn=html=>[...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(m=>JSON.parse(m[1]));
  const metaOf=(html,k)=>unent(html.match(new RegExp(`<meta (?:name|property)="${k}" content="([^"]*)"`))[1]);
  // Within 40 characters before, a negation; for the Chinese, within 12.
  const negatedEn=(text,re,where)=>{for(const m of text.matchAll(re)) assert.match(text.slice(Math.max(0,m.index-40),m.index),/\bnot\b|\bno\b|n’t|n't/,where+': "'+m[0]+'" reads as a claim: '+text.slice(Math.max(0,m.index-60),m.index+40));};
  const negatedZh=(text,re,where)=>{for(const m of text.matchAll(re)) assert.match(text.slice(Math.max(0,m.index-12),m.index),/不是|并非|不要|没有|不能/,where+': "'+m[0]+'" reads as a claim: '+text.slice(Math.max(0,m.index-30),m.index+20));};
  const fmtFig=(v,f='pct1')=>fmt[f](v);
  // A figure printed from its leaf, with or without the class the parity check reads.
  const hasFig=(h,f,x)=>[`">`,`" class="metric">`,`" class="num">`,`" class="fig">`].some(m=>h.includes(`data-fig="large-source-update.json|${f}|${x}${m}${fmt[f](x)}<`));
  // Accuracy never alone: every place an arm's accuracy is printed, that arm's balanced accuracy
  // is printed within 220 characters, before or after it.
  const accBesideBa=(text,where)=>{for(const c of coh) for(const a of arms){
    const acc=fmtFig(C[c].arms[a].accuracy.mean),ba=fmtFig(C[c].arms[a].balanced_accuracy.mean);
    let i=-1,seen=0;
    while((i=text.indexOf(acc,i+1))>=0){seen++;
      assert.ok(text.slice(Math.max(0,i-220),i+220).includes(ba),where+': '+c+' '+a+' accuracy '+acc+' printed without its balanced accuracy '+ba+' beside it');}
  }};
  const DSEC=(html,c)=>{const a=html.indexOf(`<section class="topic-section" id="${c.toLowerCase()}"`);assert.ok(a>0,'the '+c+' section must render');return html.slice(a,html.indexOf('</section>',a));};
  for(const [label,path] of [['en','topics/sleep-staging/'],['zh','zh/topics/sleep-staging/']]){
    const zh=label==='zh',html=pageOf(path),where=label+'/sleep-staging';
    const main=html.slice(html.indexOf('<section class="topic-hero">'),html.indexOf('<nav class="topic-switcher"'));
    const text=visible(main),desc=metaOf(html,'description');
    // Every figure-like token on the page, and in its description, comes from the Dreem result.
    for(const t of [...figureLike(text),...figureLike(desc)]) assert.ok(drTokens.has(t),where+': "'+t+'" is not a value of the Dreem export');
    // Both cohorts, each in its own section, in that order, and nothing pooled.
    assert.ok(main.indexOf('id="dod-h"')>0&&main.indexOf('id="dod-o"')>main.indexOf('id="dod-h"'),where+': DOD-H then DOD-O, each its own section');
    for(const c of coh){
      const sec=DSEC(html,c),k=C[c];
      for(const a of arms) for(const m of ['accuracy','balanced_accuracy','macro_f1','cohen_kappa']){
        const v=k.arms[a][m],f=m==='cohen_kappa'?'num3':'pct1';
        const at=sec.indexOf(`data-cell="${c}|${a}|${m}"`),cell=sec.slice(at,sec.indexOf('</td>',at));
        assert.ok(at>0,where+': '+c+' '+a+' '+m+' cell');
        for(const x of [v.mean,...v.interval_95]) assert.ok(hasFig(cell,f,x),where+': '+c+' '+a+' '+m+' '+x);
      }
      // Accuracy and balanced accuracy in the same row of the table.
      for(const a of arms){const at=sec.indexOf(`<tr data-arm="${c}|${a}">`),row=sec.slice(at,sec.indexOf('</tr>',at));
        assert.ok(row.includes(`data-cell="${c}|${a}|accuracy"`)&&row.includes(`data-cell="${c}|${a}|balanced_accuracy"`),where+': '+c+' '+a+' accuracy and balanced accuracy share a row');}
      // The paired gain with its interval, and what it is.
      const d=k.paired_balanced_accuracy,fd=sec.slice(sec.indexOf(`data-paired="${c}"`));
      assert.ok(hasFig(fd,'pp1',d.mean)&&fd.includes(`|sgn1|${d.interval_95[0]}"`)&&fd.includes(`|pp1|${d.interval_95[1]}"`),where+': '+c+' paired gain and interval');
      assert.match(visible(fd).slice(0,600),zh?/区间不含零/:/it excludes zero/,where+': '+c+' the paired interval excludes zero, said so');
      // Per stage: every value with its support, a null as a dash with its reason — never a zero.
      for(const st of k.arms.spectral_ridge.per_stage){
        const tr0=sec.indexOf(`<tr data-stage="${c}|${st.stage}">`);
        assert.ok(tr0>0&&sec.slice(tr0,sec.indexOf('</th>',tr0)).includes(`data-fig="large-source-update.json|count|${st.support_epochs}"`),where+': '+c+' '+st.stage+' support epochs');
        for(const key of ['recall','precision','f1']){
          const m=st[key],at=sec.indexOf(`data-cell="${c}|${st.stage}|${key}"`),cell=sec.slice(at,sec.indexOf('</td>',at));
          assert.ok(at>0,where+': '+c+' '+st.stage+' '+key+' cell');
          if(m.mean===null){
            assert.ok(cell.includes('data-null="true"')&&cell.includes('<span class="metric">—</span>'),where+': '+c+' '+st.stage+' '+key+' is null: a dash');
            assert.doesNotMatch(visible(cell),/\d+\.\d%|\b0\b(?! nights| 晚)/,where+': '+c+' '+st.stage+' '+key+' is null: never printed as a number');
            assert.match(visible(cell),zh?/没有定义：.*没有一晚预测过/:/not defined: .* was never predicted on any of the/,where+': '+c+' '+st.stage+' '+key+' says why it is not defined');
          } else {
            assert.ok(!cell.includes('data-null')&&hasFig(cell,'pct1',m.mean),where+': '+c+' '+st.stage+' '+key+' value');
            if(m.nights_defined<k.nights) assert.ok(cell.includes(`|count|${m.nights_defined}"`),where+': '+c+' '+st.stage+' '+key+' says on how many nights it is defined');
          }
        }
      }
      assert.equal((sec.match(/data-null="true"/g)||[]).length,k.arms.spectral_ridge.per_stage.reduce((n,st)=>n+['recall','precision','f1'].filter(x=>st[x].mean===null).length,0),where+': '+c+' one dash per null, no more');
      // The stage it never predicts, named in words.
      const nv=sec.slice(sec.indexOf(`data-never="${c}"`));
      for(const s0 of k.arms.spectral_ridge.stages_never_predicted) assert.match(visible(nv).slice(0,400),new RegExp(zh?`没有一晚预测过 ${s0}`:`predicted ${s0} on none of the`),where+': '+c+' never predicts '+s0);
      // Cohort accounting in the lede: nights, eligible epochs, folds, tested and trained per fold.
      const lede=sec.slice(0,sec.indexOf('class="interval-plot"'));
      for(const v of [k.nights,k.eligible_epochs,k.folds,k.nights_tested_per_fold,k.nights_trained_per_fold]) assert.ok(lede.includes(`|count|${v}"`),where+': '+c+' lede count '+v);
      // No chance line on the plot: the prior is a floor.
      assert.doesNotMatch(sec,/class="ip-ref"/,where+': '+c+' plot draws no chance line');
    }
    // The short answer: the ridge's accuracy beside its balanced accuracy, the prior's too, N1 never predicted.
    const ans=visible(html.slice(html.indexOf('<section class="short-answer"'),html.indexOf('</section>',html.indexOf('<section class="short-answer"'))));
    for(const c of coh) for(const a of arms) for(const m of ['accuracy','balanced_accuracy']) assert.ok(ans.includes(pct1(C[c].arms[a][m].mean)),where+': the short answer gives '+c+' '+a+' '+m);
    assert.match(ans,zh?/从未预测过 N1/:/never predicted N1 in either/,where+': the short answer says N1 is never predicted');
    // Accuracy never without balanced accuracy beside it: page text and description.
    accBesideBa(text,where);accBesideBa(desc,where+' description');
    // No chance label on the prior's balanced accuracy: every mention of chance is a denial.
    if(zh) negatedZh(chineseOnly(main).replace(/<[^>]+>/g,' '),/随机水平/g,where); else negatedEn(text+' '+desc,/chance/gi,where);
    // No cross-cohort comparison wording.
    assert.doesNotMatch(text,zh?/(?:比(?!较)|低于|高于|不如|优于|好于|差于)[^。；]{0,20}(?:DOD-[HO]|健康被试|呼吸暂停)|(?:DOD-[HO]|健康被试|呼吸暂停患者)[^。；]{0,30}(?:低于|高于|不如|优于|好于|差于|更低|更高)/
      :/\b(?:DOD-[HO]|healthy|apn(?:o)?ea|OSA)\b[^.;:]{0,60}\b(?:lower|higher|worse|better|less|more|drops?|fell|falls)\b[^.;:]{0,30}\bthan\b|\b(?:than|versus|vs\.?|compared (?:with|to))\b[^.;:]{0,40}\b(?:DOD-[HO]|healthy|apn(?:o)?ea|OSA)\b/i,where+': no cross-cohort comparison');
    assert.match(text,zh?/本页不对两者做任何比较/:/nothing on this page compares them/,where+': the page says it compares the cohorts nowhere');
    assert.match(text,zh?/不是对健康状况的受控比较/:/not a controlled comparison of health status/,where+': not a disease effect');
    assert.match(text,zh?/没有测量从一个队列到另一个队列的迁移/:/nothing here measures transfer from one cohort to the other/,where+': not transfer');
    // No clinical or diagnostic claim; the claim boundary stated.
    assert.doesNotMatch(text,zh?/可以诊断|用于诊断|诊断准确率|达到(?:人类)?专家水平|临床级/:/diagnostic accuracy|can diagnose|clinical[- ]grade|expert[- ]level|human[- ]level|as good as (?:a )?(?:human|expert)/i,where+': no diagnostic or clinical claim');
    assert.match(text,zh?/不是临床，也不是诊断/:/Not clinical, not a diagnosis/,where+': the claim boundary');
    // The required limits.
    for(const re of zh?[/毫伏[^。]*微伏/,/不能说明校准、参考、削波或滤波是否等价/,/不是经过校准的概率/,/略高于五分之一/,/不要把这些数字与使用其他通道、队列、预处理或数据划分的论文相比/]
                     :[/millivolts[^.]*microvolts/,/does not establish that calibration, reference, clipping or filtering are equivalent/,/not calibrated probabilities/,/slightly above one fifth/,/Do not compare these figures with papers that use other channels, cohorts, preprocessing or splits/])
      assert.match(text,re,where+': limit '+re);
    // Cohort and design: the accounting, the folds, the features and the bootstrap.
    const design=html.slice(html.indexOf('id="design"'),html.indexOf('id="held"'));
    for(const v of [ra.archive_records,ra.excluded_before_scoring,ra.evaluated,ea.total,ea.unscored,ea.zero_or_invalid_channel_scale,ea.eligible,dr.jobs.trained])
      assert.ok(hasFig(design,'count',v),where+': design count '+v);
    for(const re of zh?[/5 个 EEG 导联（C3-M2、F3-F4、F3-M2、F3-O1、F4-O2）/,/每帧 25 个数值/,/alpha 为 1/,/每个队列内部分为 5 折/,/10,000 次抽样/,/整晚 bootstrap/]
                     :[/Five EEG derivations \(C3-M2, F3-F4, F3-M2, F3-O1, F4-O2\)/,/25 values per epoch/,/alpha 1/,/Five folds within each cohort/,/10,000 draws/,/whole-night bootstrap/])
      assert.match(visible(design),re,where+': design '+re);
    // The hold: figure-free, on the page and linked to its register row.
    const held=html.slice(html.indexOf('id="held"'),html.indexOf('id="methods-and-limits"'));
    assert.ok(held.length>400&&!/\d/.test(visible(held)),where+': the hold note renders, figure-free');
    assert.match(visible(held),zh?/基础模型和其他对幅值敏感的编码器暂缓/:/Foundation models and other amplitude-sensitive encoders are held because the source’s physical units disagree/,where+': the hold says why');
    assert.ok(held.includes(`href="${zh?'/zh':''}/releases/#hold-dreem-amplitude-sensitive-models"`),where+': the hold links its register row');
    // Credits and rights: paper, deposit, pinned revision, licence as the deposit declares it, and
    // per cohort exactly what the paper states and what is missing.
    for(const s0 of ['10.1109/TNSRE.2020.3011181','10.5281/zenodo.15900394','arxiv.org/abs/1911.03221',dr.credits.repository_revision,`${dr.credits.repository}/tree/${dr.credits.repository_revision}`,'Guillot','https://opensource.org/licenses/MIT'])
      assert.ok(html.includes(s0),where+': credit '+s0);
    assert.match(text,zh?/存档许可：MIT，依据 Zenodo 记录上的声明/:/Deposit licence: MIT, as declared on the Zenodo record/,where+': the deposit licence, as declared');
    const consent=html.slice(html.indexOf('data-consent="cohorts"'),html.indexOf('</article>',html.indexOf('data-consent="cohorts"')));
    for(const c of coh){
      const ce=C[c].consent_and_ethics,p0=consent.slice(consent.indexOf(`data-consent-cohort="${c}"`),consent.indexOf('</p>',consent.indexOf(`data-consent-cohort="${c}"`)));
      for(const x of [ce.ethics_approval,ce.informed_consent]) assert.ok(unent(p0).includes(x.stated?x.statement:x.note),where+': '+c+' the paper\'s statement as recorded: '+(x.statement??x.note).slice(0,50));
      const missing=!ce.ethics_approval.stated?(zh?'伦理批准：未说明。':'Ethics approval: not stated.'):(zh?'知情同意：未说明。':'Informed consent: not stated.');
      assert.ok(visible(p0).includes(missing),where+': '+c+' says which statement is missing');
    }
    assert.equal(C['DOD-H'].consent_and_ethics.ethics_approval.stated&&!C['DOD-H'].consent_and_ethics.informed_consent.stated&&C['DOD-O'].consent_and_ethics.informed_consent.stated&&!C['DOD-O'].consent_and_ethics.ethics_approval.stated,true,'the export states DOD-H ethics without consent, DOD-O consent without a committee');
    assert.ok(html.includes('href="/data/large-source-update.json"'),where+': the reviewed export is linked');
  }
  // Same figures in both languages: every data-fig on each new section, as a multiset.
  const figSet=html=>[...html.matchAll(/data-fig="([^"]+)"/g)].map(m=>m[1]).sort();
  assert.deepEqual(figSet(pageOf('zh/topics/sleep-staging/')),figSet(pageOf('topics/sleep-staging/')),'sleep-staging: the same figures in both languages');
  const nsOf=html=>{const a=html.indexOf('<section class="topic-section" id="next-session"');assert.ok(a>0,'calibration-budget: the next-session section must render');return html.slice(a,html.indexOf('</section>',a));};
  assert.deepEqual(figSet(nsOf(pageOf('zh/topics/calibration-budget/'))),figSet(nsOf(pageOf('topics/calibration-budget/'))),'calibration-budget #next-session: the same figures in both languages');

  // OpenBMI on calibration-budget, #next-session.
  for(const [label,path] of [['en','topics/calibration-budget/'],['zh','zh/topics/calibration-budget/']]){
    const zh=label==='zh',html=pageOf(path),where=label+'/calibration-budget';
    const sec=nsOf(html),stext=visible(sec);
    assert.ok(html.indexOf('id="next-session"')<html.indexOf('id="methods-and-limits"')&&html.indexOf('id="next-session"')>html.indexOf('id="trca-heading"'),where+': #next-session sits after the SSVEP evidence, before methods and limits');
    for(const t of figureLike(stext)) assert.ok(obTokens.has(t),where+': "'+t+'" in #next-session is not a value of the OpenBMI export');
    assert.match(stext,zh?/所以这里不与它们比较/:/so nothing here is compared with them/,where+': not compared with the SSVEP figures');
    // Cohort accounting: 54 = 1 + 2 + 51, 3,060 held-out trials, 408 jobs, 60 per person.
    for(const v of [ob.cohort.acquisition_identities,ob.cohort.engineering_exclusion,ob.cohort.input_quality_holds,ob.cohort.evaluated,ob.cohort.unique_test_trials,ob.cohort.jobs.trained,ob.cohort.test_trials_each_person])
      assert.ok(hasFig(sec,'count',v),where+': cohort count '+v);
    // The protocol: session 1 fits and calibrates, the first 0/10/20/40 of session 2 calibrate, the same final 60 test.
    for(const re of zh?[/前 80 个试次拟合分类器，后 20 个用于概率校准/,/第二次会话最前面的 0、10、20 或 40 个校准试次/,/每档预算都在这些相同的试次上测试/]
                     :[/the first 80 trials fit it, the last 20 calibrate its probabilities/,/the first 0, 10, 20 or 40 labeled trials of their session 2/,/Every budget is tested on those same trials/])
      assert.match(stext,re,where+': protocol '+re);
    assert.ok(hasFig(sec,'pct1',ob.chance_level),where+': chance level');
    // The budget table: both arms, every budget, balanced accuracy with its interval.
    for(const a of ob.arms) for(const b of a.by_budget){
      const at=sec.indexOf(`data-cell="${a.id}|${b.target_trials}"`),cell=sec.slice(at,sec.indexOf('</td>',at));
      for(const x of [b.balanced_accuracy.mean,...b.balanced_accuracy.interval_95]) assert.ok(at>0&&hasFig(cell,'pct1',x),where+': '+a.id+' at '+b.target_trials+': '+x);
    }
    // Every mean change has how many people declined beside it, and a change whose interval
    // includes zero says it is not established — in the table, the finding, the short answer and
    // the description.
    for(const a of ob.arms) for(const g of a.calibration_gain){
      const at=sec.indexOf(`data-gain="${a.id}|${g.target_trials}"`),cell=sec.slice(at,sec.indexOf('</td>',at)),ch=g.balanced_accuracy_change;
      assert.ok(at>0,where+': gain cell '+a.id+' '+g.target_trials);
      for(const [f,x] of [['pp1',ch.mean],['sgn1',ch.interval_95[0]],['pp1',ch.interval_95[1]],['count',g.people_with_any_decline],['count',g.people],['count',g.people_with_decline_of_5_points_or_more]])
        assert.ok(hasFig(cell,f,x),where+': gain '+a.id+' '+g.target_trials+' prints '+f+' '+x);
      assert.equal(cell.includes('data-not-established'),!g.interval_excludes_zero,where+': gain '+a.id+' '+g.target_trials+' "not established" exactly when its interval includes zero');
      if(!g.interval_excludes_zero) assert.match(visible(cell),zh?/区间包含零：不能认定/:/The interval includes zero: not established/,where+': gain '+a.id+' '+g.target_trials+' not established, in words');
    }
    const ans=visible(html.slice(html.indexOf('<section class="short-answer"'),html.indexOf('</section>',html.indexOf('<section class="short-answer"'))));
    const declineRe=(k,n)=>zh?new RegExp(`(?<![\\d.,])${k} 人`):new RegExp(`(?<![\\d.,])${k} (?:of ${n}\\b|of them|people|declined)`);
    for(const [where2,t] of [['page',visible(html)],['description',metaOf(html,'description')],['og:description',metaOf(html,'og:description')]])
      for(const a of ob.arms) for(const g of a.calibration_gain){
        const s0=pp1(g.balanced_accuracy_change.mean);let i=-1;
        while((i=t.indexOf(s0,i+1))>=0){
          // Only the OpenBMI changes: the SSVEP section prints no pp of these values (checked by the token rule above for #next-session).
          assert.match(t.slice(Math.max(0,i-120),i+320),declineRe(g.people_with_any_decline,g.people),where+' '+where2+': '+a.id+' '+g.target_trials+' mean change '+s0+' printed without how many people declined');
          if(!g.interval_excludes_zero) assert.match(t.slice(i,i+260),zh?/不能认定/:/not established/,where+' '+where2+': '+s0+' is not established, and must say so');
        }
      }
    for(const s0 of [pp1(lc40.balanced_accuracy_change.mean),pp1(psd40.balanced_accuracy_change.mean),String(lc40.people_with_any_decline),String(psd40.people_with_any_decline),String(ob.cohort.evaluated)])
      assert.ok(ans.includes(s0),where+': the short answer gives '+s0);
    assert.match(ans,zh?/只用一个固定频带，而不是原方法的滤波器组/:/one fixed band, not the original method's filter bank/,where+': the SSVEP caveat stays in the short answer');
    // An expanded cohort, not a replication; the earlier snapshot is history, with no figure.
    const coh0=visible(sec.slice(sec.indexOf('id="next-session-cohort"'),sec.indexOf('</p>',sec.indexOf('id="next-session-cohort"'))));
    assert.match(coh0,zh?/不是独立的重复验证/:/not an independent replication/,where+': expanded cohort, not a replication');
    assert.match(coh0,zh?/从未在本站发布/:/never published here/,where+': the earlier snapshot is history');
    for(const v of [ob.cohort.original_people,ob.cohort.added_people,ob.cohort.evaluated]) assert.ok(sec.includes(`|count|${v}"`),where+': cohort history count '+v);
    // The required limits.
    const lim=visible(sec.slice(sec.indexOf('id="next-session-limits"')));
    for(const re of zh?[/一个数据集，离线/,/不是新被试/,/两个固定的 CPU 基线/,/只基于 60 个测试试次/,/物理幅值单位尚未确定/]
                     :[/One dataset, offline/,/Not a new person/,/Two fixed CPU baselines/,/rests on 60 test trials/,/physical amplitude unit is not resolved/])
      assert.match(lim,re,where+': next-session limit '+re);
    // Credits and rights: the paper, the data DOI, CC0 1.0, the IRB and written consent.
    for(const s0 of ['10.1093/gigascience/giz002','https://doi.org/10.5524/100542','CC0-1.0','https://creativecommons.org/publicdomain/zero/1.0/']) assert.ok(sec.includes(s0),where+': OpenBMI credit '+s0);
    assert.match(stext,zh?/高丽大学（Korea University）机构审查委员会批准（1040548-KUIRB-16-159-A-2），所有被试在实验前都签署了书面知情同意/:/approval by the Korea University Institutional Review Board \(1040548-KUIRB-16-159-A-2\) and written informed consent from all participants/,where+': IRB and written consent');
    assert.ok(sec.includes('href="/data/large-source-update.json"'),where+': the reviewed export is linked');
  }
  // The SSVEP pins on calibration-budget stay as they were (the checks above it), and the
  // question is the broadened one in the title, the card and the markup.
  {
    const ld=ldIn(pageOf('topics/calibration-budget/'))[0]['@graph'];
    const node=ld.find(n=>n['@type']==='Dataset');
    assert.deepEqual(node.distribution.map(d=>d.contentUrl).sort(),['https://bci.report/data/deployment-topics.json','https://bci.report/data/large-source-update.json'],'calibration-budget: distribution names both exports');
    assert.equal(ld.find(n=>n['@type']==='FAQPage').mainEntity[0].name,'How much calibration data does an EEG decoder need?','calibration-budget: the FAQ question is the broadened one');
    const sl=ldIn(pageOf('topics/sleep-staging/'))[0]['@graph'].find(n=>n['@type']==='Dataset');
    assert.deepEqual(sl.distribution.map(d=>d.contentUrl),['https://bci.report/data/large-source-update.json'],'sleep-staging: distribution');
    assert.equal(sl.version,ls.release_id,'sleep-staging: the Dataset version is the batch');
  }
  // model-adaptation's next-day section now points to the next-session result, figure-free.
  for(const p of ['topics/model-adaptation/','zh/topics/model-adaptation/']){
    const html=pageOf(p),at=html.indexOf('id="next-session-pointer"'),ptr=html.slice(at,html.indexOf('</p>',at));
    assert.ok(at>html.indexOf('id="next-day"')&&ptr.includes(`href="${p.startsWith('zh')?'/zh':''}/topics/calibration-budget/#next-session"`)&&!/\d/.test(visible(ptr)),p+': the next-day section points to #next-session, figure-free');
  }

  // Dataset pages: Dreem has one group per cohort and none for both; accuracy rows sit next to the
  // same arm's balanced-accuracy rows; no chance level; no row for a null.
  for(const [label,pfx] of [['en',''],['zh','zh/']]){
    const zh=label==='zh',dd=pageOf(pfx+'datasets/dreem-dod/'),where=label+'/datasets/dreem-dod';
    const groups=[...dd.matchAll(/<section class="entity-group" id="g-([^"]+)"/g)].map(m=>m[1]);
    assert.deepEqual(groups,['dreem-dod-h','dreem-dod-o'],where+': one group per cohort, nothing pooled');
    for(const c of coh){
      const g0=dd.indexOf(`id="g-dreem-${c.toLowerCase()}"`),g=dd.slice(g0,dd.indexOf('</section>',g0));
      const meta=g.slice(0,g.indexOf('</p>'));
      assert.doesNotMatch(meta,/Chance level|随机水平/,where+': '+c+' no chance level for the prior to be read against');
      assert.doesNotMatch(g,/class="ip-ref"/,where+': '+c+' no chance line');
      const rows=[...g.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(m=>m[1]);
      for(const a of arms){
        const ar=C[c].arms[a],acc=`|pct1|${ar.accuracy.mean}"`,ba=`|pct1|${ar.balanced_accuracy.mean}"`;
        const i=rows.findIndex(r=>r.includes(acc));
        assert.ok(i>0&&(rows[i-1].includes(ba)||rows[i+1]?.includes(ba)),where+': '+c+' '+a+' accuracy row sits beside its balanced-accuracy row');
      }
      const nulls=C[c].arms.spectral_ridge.per_stage.filter(st=>st.precision.mean===null).map(st=>st.stage);
      for(const s0 of nulls){
        assert.ok(!rows.some(r=>r.includes(zh?`${s0} 期`:`stage ${s0}`)&&/>(?:Precision|精确率)</.test(r)),where+': '+c+' '+s0+' precision is null: no row');
        assert.ok(rows.some(r=>r.includes(zh?`${s0} 期`:`stage ${s0}`)&&(zh?/精确率没有定义（不是零）/:/precision is not defined \(not zero\)/).test(unent(r))),where+': '+c+' '+s0+' the recall row says its precision is not defined, not zero');
      }
      accBesideBa(visible(g),where+' '+c);
    }
    if(zh) negatedZh(chineseOnly(dd).replace(/<[^>]+>/g,' '),/随机水平/g,where); else negatedEn(visible(dd),/chance/gi,where);
    assert.ok(dd.includes('10.1109/TNSRE.2020.3011181')&&dd.includes('10.5281/zenodo.15900394')&&dd.includes('https://opensource.org/licenses/MIT'),where+': credit and licence');
    // OpenBMI: every mean change with the people who declined, in order, and "not established" where due.
    const op=pageOf(pfx+'datasets/openbmi/'),wo=label+'/datasets/openbmi';
    assert.ok(op.includes('id="g-openbmi-cross-session-calibration"'),wo+': the group');
    for(const a of ob.arms) for(const g of a.calibration_gain){
      const at=op.indexOf(`data-fig="large-source-update.json|pp1|${g.balanced_accuracy_change.mean}"`),end=op.indexOf('</tr>',at);
      const n0=op.indexOf('class="row-note"',at),note=n0>0&&n0<end?op.slice(n0,end):'';
      assert.ok(at>0&&note,wo+': '+a.id+' '+g.target_trials+' the change carries its reading');
      assert.deepEqual([...note.matchAll(/data-fig="large-source-update\.json\|count\|(\d+)"/g)].map(m=>Number(m[1])),[g.people_with_any_decline,g.people,g.people_with_decline_of_5_points_or_more],wo+': '+a.id+' '+g.target_trials+' the people behind the mean, in order');
      assert.equal((zh?/这一提升不能认定/:/not established/).test(note),!g.interval_excludes_zero,wo+': '+a.id+' '+g.target_trials+' "not established" exactly when due');
    }
    assert.ok(op.includes('10.1093/gigascience/giz002')&&op.includes('CC0-1.0'),wo+': credit and licence');
    assert.ok(op.includes(`data-fig="large-source-update.json|pct1|${ob.chance_level}"`),wo+': chance level, a real one here');
    // The index: both, with their people.
    const idx=pageOf(pfx+'datasets/');
    for(const [slug,people] of [['dreem-dod','25 / 55'],['openbmi','51']]){
      const at=idx.indexOf(`href="/${pfx}datasets/${slug}/"`),row=idx.slice(at,idx.indexOf('</tr>',at));
      assert.ok(at>0&&row.includes(`<td>${people}</td>`),label+'/datasets/: '+slug+' listed with '+people+' people');
    }
  }
  // Releases: the batch, its manifest hash, the hold (open, figure-free, linking its section).
  for(const [label,path] of [['en','releases/'],['zh','zh/releases/']]){
    const html=pageOf(path);
    assert.ok(html.includes(`id="${ls.release_id}"`)&&html.includes(ls.provenance.manifest_sha256),label+': the large-source release and its manifest');
    const at=html.indexOf('<tr id="hold-dreem-amplitude-sensitive-models" class="hold-open">'),row=html.slice(at,html.indexOf('</tr>',at));
    assert.ok(at>0,label+': the Dreem hold is in the register, open');
    assert.ok(!/\d/.test(visible(row.slice(row.lastIndexOf('<td>')))),label+': the hold\'s reason carries no figure');
    assert.ok(row.includes(`href="${label==='zh'?'/zh':''}/topics/sleep-staging/#held"`),label+': the hold links its section');
  }
  // Home: the hold card, figure-free; the transfer map's held entry; the card counts are pinned above.
  for(const [label,path] of [['en',''],['zh','zh/']]){
    const html=pageOf(path),at=html.indexOf(`<a class="hold-card" href="${label==='zh'?'/zh':''}/topics/sleep-staging/#held"`),card=html.slice(at,html.indexOf('</a>',at));
    assert.ok(at>0&&!/\d/.test(visible(card.replace(/<small>[\s\S]*<\/small>/,''))),label+': the home hold card, figure-free');
    for(const page of [path,path+'topics/']){
      const t=pageOf(page),li=t.slice(t.indexOf('<li data-map="person:dreem-amplitude-sensitive-models">'),t.indexOf('</li>',t.indexOf('<li data-map="person:dreem-amplitude-sensitive-models">')));
      assert.ok(li.length>20&&li.includes(`href="${label==='zh'?'/zh':''}/releases/#hold-dreem-amplitude-sensitive-models"`)&&!/\d/.test(visible(li)),(page||'/')+': the held map entry, figure-free');
    }
  }
  // Data use (English only): the batch's sources, licences and the per-cohort statements.
  {
    const du=pageOf('data-use/'),sec=du.slice(du.indexOf('id="sources-2026-10-03"'),du.indexOf('</section>',du.indexOf('id="sources-2026-10-03"')));
    assert.ok(sec.length>1000,'data-use: the 3 October section');
    for(const s0 of [dr.rights.name,ob.rights.name,'MIT','CC0-1.0',dr.cohorts['DOD-H'].consent_and_ethics.informed_consent.note,dr.cohorts['DOD-O'].consent_and_ethics.ethics_approval.note])
      assert.ok(unent(sec).includes(s0),'data-use: '+s0.slice(0,60));
  }
  assert.ok(llms.includes('https://bci.report/datasets/dreem-dod/index.md')&&llms.includes('https://bci.report/datasets/openbmi/index.md'),'llms.txt: the two new dataset pages');
  // The new and broadened topics name the new dataset pages on their Measured-on line, and their
  // cite blocks the batch's release; the dataset pages cite that release alone.
  for(const [label,pfx] of [['en',''],['zh','zh/']]){
    for(const [slug,ds] of [['sleep-staging','dreem-dod'],['calibration-budget','openbmi']]){
      const html=pageOf(pfx+'topics/'+slug+'/'),at=html.indexOf('<p class="topic-entities">'),line=html.slice(at,html.indexOf('</p>',at));
      assert.ok(at>0&&line.includes(`href="/${pfx}datasets/${ds}/"`),label+'/'+slug+': the Measured on line links /datasets/'+ds+'/');
      const cite=html.slice(html.indexOf('<section class="cite-page"'));
      assert.ok(cite.match(/data-releases="([^"]+)"/)[1].split(' ').includes(ls.release_id),label+'/'+slug+': the cite block names '+ls.release_id);
    }
    // Since 2026-10-07 the OpenBMI page also prints route 2's group, so it names that release too, newest first.
    for(const [ds,rels] of [['dreem-dod',[ls.release_id]],['openbmi',['shared-representation-update-20261007',ls.release_id]]]){
      const html=pageOf(pfx+'datasets/'+ds+'/'),cite=html.slice(html.indexOf('<section class="cite-page"'));
      assert.equal(cite.match(/data-releases="([^"]+)"/)[1],rels.join(' '),label+'/datasets/'+ds+': the cite block names exactly the releases its figures come from');
      assert.ok(html.includes('class="entity-profile"'),label+'/datasets/'+ds+': the sourced profile renders');
    }
  }
}
console.log('PASS: 2026-10-03 large-source — Dreem on its own question: DOD-H and DOD-O apart, accuracy never without balanced accuracy, nulls as dashes with their reason, the prior a floor and never a chance level, no cross-cohort or clinical claim, accounting, design, figure-free hold, credits and per-cohort consent and ethics; OpenBMI on calibration-budget: accounting, protocol, budget table, every mean change with how many people declined, "not established" where the interval includes zero, expanded cohort not replication; every figure from the export, the same in both languages; dataset pages, register, home, map and data use.');

// --- Protocol pages (2026-10-02) -------------------------------------------------
// Each core-matrix protocol has its own address in both languages, built from the
// released track. Seven of the eight were reachable only through JavaScript. Their
// figures are re-read above from the protocol's own results CSV and protocol JSON;
// what is checked here is that nothing is missing and that the caveats travel.
{
  const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const figsOf=html=>[...html.matchAll(/data-fig="([^"]+)"[^>]*>([^<]*)</g)].map(m=>m[1]+' → '+m[2]);
  const allNames=[...new Set(data.tracks.flatMap(t=>t.rows.map(r=>r.name)))];
  // The home page's protocol dialog in each language, run as above, for comparison with these pages.
  const dialogIn=lang=>{
    const els=new Map(),g=s=>{if(!els.has(s))els.set(s,new Element());return els.get(s);};
    g('#family-filter').value='all';g('#sort-results').value='name';g('#fm-rows').textContent=fmEmbedded(lang.startsWith('zh')?'zh':'en');
    vm.runInNewContext(stripTypeScriptTypes(source),{data,document:{querySelector:g,querySelectorAll:()=>[],documentElement:{lang}},window:{addEventListener(){}},AbortController,Promise,console});
    return id=>{g('#track-tabs').events.click({target:{closest:()=>({dataset:{track:id}})}});g('#open-protocol').events.click();return g('#dialog-body').innerHTML;};
  };
  const dialogs={en:dialogIn('en'),zh:dialogIn('zh-Hans')};
  const textOf=s=>s.replace(/<[^>]+>/g,'').replace(/\s+/g,' ').trim();
  // The sleep protocol's consent caveat, as each language states it.
  const consentCaveat={
    en:'According to the 2025 data descriptor, the informed consent form did not mention publication, and before release the GDPR office of Region Midt judged the data fully anonymised: consent covered the study, and the public release rests on that anonymisation judgement.',
    zh:'据 2025 年的数据描述论文，知情同意书没有提到公开发布；发布前，Region Midt（丹麦中部大区）的 GDPR 办公室判定这些数据已完全匿名化：同意书覆盖的是研究本身，公开发布依据的是这一匿名化判定。'};
  const resolves=href=>{const p=href.slice(1).split('?')[0];
    if(p===''||p.endsWith('/'))return existsSync(new URL(p+'index.html',DIST));
    return existsSync(new URL(p,DIST))||existsSync(new URL(p+'.html',DIST))||existsSync(new URL(p+'/index.html',DIST));};
  for(const [label,prefix] of [['en',''],['zh','zh/']]){
    assert.ok(existsSync(new URL(prefix+'protocols/index.html',DIST)),label+': the protocols index must exist');
    const index=pageOf(prefix+'protocols/');
    assert.equal((index.match(/<tr data-protocol=/g)||[]).length,data.tracks.length,label+': the index lists every protocol once');
    for(const t of data.tracks){
      assert.ok(index.includes(`href="/${prefix}protocols/${t.id}/"`),label+': the index links '+t.id);
      assert.ok(index.includes(`data-fig="${t.id}-protocol.json|count|${t.subjects}"`),label+': the index prints the '+t.id+' cohort from its file');
      if(t.chanceLevel!=null) assert.ok(index.includes(`data-fig="${t.id}-protocol.json|pct1raw|${t.chanceLevel}"`),label+': the index prints the '+t.id+' chance level');
    }
    assert.match(index,label==='en'?/not a failure/:/不是失败/,label+': the index keeps the blank-cell caveat');
    for(const [,href] of index.matchAll(/href="(\/[^"#]*)/g)) assert.ok(resolves(href),label+': protocols index link '+href+' does not resolve');
    // The home matrix's column headings lead here, in the reader's language.
    const homePage=pageOf(prefix);
    for(const t of data.tracks)
      assert.ok(homePage.includes(`href="/${prefix}protocols/${t.id}/" data-jump="${t.id}"`),label+': matrix heading '+t.id+' must link its protocol page');
  }
  const unesc=s=>s.replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
  const dirZhText=JSON.parse(readFileSync(new URL('../src/data/directory-zh.json',import.meta.url),'utf8')).text;
  for(const t of data.tracks){
    const path='protocols/'+t.id+'/', csv=t.id+'-results.csv', pj=t.id+'-protocol.json';
    for(const p of [path,'zh/'+path]) assert.ok(existsSync(new URL(p+'index.html',DIST)),p+': protocol page missing');
    // The released results file, row by row: header names, then one record per method.
    const [csvHead,...csvBody]=csvRows(readFileSync(new URL('data/'+csv,DIST),'utf8')).filter(r=>r.length>1);
    const csvRecords=csvBody.map(r=>Object.fromEntries(csvHead.map((k,i)=>[k,r[i]])));
    const en=pageOf(path),zh=pageOf('zh/'+path);
    assert.ok(en.includes('<h1>'+esc(t.title+' on '+t.dataset)+'</h1>'),path+': the h1 names the protocol and its dataset');
    assert.ok(zh.includes('（'+esc(t.dataset)+'）</h1>'),'zh/'+path+': the h1 names the dataset');
    assert.ok(en.includes('<title>'+esc(t.title+' on '+t.dataset)+' — EEG decoding results with their protocol'),path+': a self-describing title');
    assert.ok(en.includes(esc(t.short)),path+': what the split generalises to');
    // Every figure, in order, identical in both languages — all of them, not only the classed ones.
    assert.ok(figsOf(en).length>t.rows.length*5,path+': the figures must carry data-fig');
    assert.deepEqual(figsOf(zh),figsOf(en),'zh/'+path+': every figure must equal the English page, in the same order');
    for(const [label,html] of [['en',en],['zh',zh]]){
      const where=(label==='zh'?'zh/':'')+path;
      // Only this protocol's own downloads back its figures.
      // Since 2026-10-04 also its v9 CSV (the new rows), and on arithmetic-rest the v9 JSON (the EEGMAT adaptation).
      assert.deepEqual([...new Set([...html.matchAll(/data-fig="([^|"]+)\|/g)].map(m=>m[1]))].sort(),
        [csv,pj,'foundation-models-'+t.id+'.csv',...(t.id==='arithmetic-rest'?['foundation-models-update.json']:[])].sort(),where+': figures must cite this protocol\'s CSV and JSON, and its v9 files');
      // Every method with a score, with every figure of its row.
      const t0=html.indexOf('class="protocol-results"'),body=html.slice(t0,html.indexOf('</tbody>',t0));
      assert.ok(t0>0,where+': the results table must render');
      assert.equal((body.match(/<tr data-row=/g)||[]).length,t.rows.length,where+': one table row per method with a score');
      for(const r of t.rows){
        const a=body.indexOf(`<tr data-row="${r.id}"`),row=body.slice(a,body.indexOf('</tr>',a));
        assert.ok(a>0&&row.includes('>'+esc(r.name)+'<'),where+': '+r.name+' must appear');
        assert.ok(row.includes('>'+esc(r.mode)+'<'),where+'/'+r.id+': training mode');
        for(const [f,v] of [['pct1raw',r.y],[t.type==='tradeoff'?'pct1raw':'num3',r.x],['s1',r.seconds],['count',r.channels],['count',r.subjects],
                            ...(r.interval?[['pct1raw',r.interval[0]],['pct1raw',r.interval[1]]]:[]),...(t.type==='tradeoff'&&r.abstain!=null?[['count',r.abstain]]:[])])
          assert.ok(row.includes(`data-fig="${csv}|${f}|${v}"`),where+'/'+r.id+': '+f+' '+v+' missing from its row');
        // The chance flags travel with the number, as on the home page.
        if(t.chanceLevel!=null&&t.type!=='tradeoff'){
          const below=label==='en'?/At or below chance level/:/不高于随机水平/, reaches=label==='en'?/Interval reaches chance level/:/区间触及随机水平/;
          if(r.y<=t.chanceLevel) assert.match(row,below,where+'/'+r.id+': at-or-below-chance must be flagged');
          else if(r.interval&&r.interval[0]<=t.chanceLevel) assert.match(row,reaches,where+'/'+r.id+': chance-touching interval must be flagged');
          else {assert.doesNotMatch(row,below,where+'/'+r.id+': flagged without cause');assert.doesNotMatch(row,reaches,where+'/'+r.id+': flagged without cause');}
        }
        if(t.seedSensitivity?.model===r.name) assert.match(row,/class="flag seed"/,where+'/'+r.id+': the single-seed flag');
        // The row is the same row of the released CSV: model and training mode, then every figure
        // in column order (primary, interval, secondary, always-abstain of participants, channels,
        // participants, scoring time). Checked against the file, not against mvp.json, and in order,
        // so two figures swapped between columns cannot pass.
        const name=unesc(row.match(/<th scope="row">([\s\S]*?)<small>/)[1].replace(/<[^>]+>/g,''));
        const mode=unesc(row.match(/<\/th><td[^>]*>([^<]*)<\/td>/)[1]);
        const rec=csvRecords.filter(x=>x.model===name&&x.evaluation_mode===mode);
        assert.equal(rec.length,1,where+'/'+r.id+': exactly one row of '+csv+' is '+name+' · '+mode);
        const c=rec[0],num=k=>Number(c[k]);
        const expected=[num('primary_percent'),...(c.descriptive_interval_low_percent!==''?[num('descriptive_interval_low_percent'),num('descriptive_interval_high_percent')]:[]),
          num('secondary_value'),...(c.always_abstain_participants!==''?[num('always_abstain_participants'),num('participants')]:[]),
          num('channels'),num('participants'),num('scoring_seconds')];
        const printed=[...row.matchAll(/data-fig="([^|"]+)\|\w+\|([^"]+)"/g)].map(m=>{assert.equal(m[1],csv,where+'/'+r.id+': a row figure from another file');return Number(m[2]);});
        assert.deepEqual(printed,expected,where+'/'+r.id+': the page row must equal the '+name+' row of '+csv+', column by column');
        if(t.type==='tradeoff'&&r.abstain>0) assert.match(row,/class="flag"><span data-fig/,where+'/'+r.id+': people who always abstained are flagged');
      }
      // Chance level from the protocol file, or the reason there is none.
      if(t.chanceLevel!=null){
        assert.ok(html.includes(`data-fig="${pj}|pct1raw|${t.chanceLevel}"`),where+': chance level');
        assert.match(html,/class="ip-ref"/,where+': the plot needs a chance reference line');
      } else assert.match(html,label==='en'?/always abstaining scores zero false activations/:/始终拒识也能得到零误触发/,where+': why detection has no chance level');
      // Plot values are the table's figures, not new ones.
      const printed=new Set([...html.matchAll(/data-fig="[^"]+"[^>]*>([^<]*)</g)].map(m=>m[1]));
      for(const [,v] of html.matchAll(/class="ip-value"><span class="fig">([^<]+)</g))
        for(const n of v.match(/\d+(?:\.\d+)?%/g)) assert.ok(printed.has(n),where+': plot value '+n+' is not a printed figure');
      // A blank matrix cell is not a failure: every matrix method without a result here is named, with that caveat.
      const n0=html.indexOf('class="protocol-note not-run"'),nr=n0<0?'':html.slice(n0,html.indexOf('</p>',n0));
      const notRun=allNames.filter(n=>!t.rows.some(r=>r.name===n));
      if(notRun.length){
        assert.ok(nr.length>0,where+': the methods not run must be listed');
        for(const n of notRun) assert.ok(nr.includes(esc(n)),where+': '+n+' must be listed as not run');
        assert.match(nr,label==='en'?/that is not a failure/:/不是失败/,where+': the blank-cell caveat');
      }
      // The protocol as released, verbatim: task, cohort, input, steps, limits, exposure, credit.
      for(const text of [t.subtitle,t.observations,t.exposure,t.limitation,t.selection,t.pretrainingOverlap,
                         t.attribution,t.rightsScope,t.protocolId,t.license,...t.protocol,...(t.seedSensitivity?[t.seedSensitivity.scope]:[])])
        assert.ok(html.includes(esc(text)),where+': payload text missing: '+String(text).slice(0,60));
      // Two exceptions, decided 2026-10-02. The privacy review reads as the reviewer's working
      // notes: the page states in one sentence what is published and links the protocol JSON,
      // which holds the full note. And a JSON fragment in the version text is printed as its fields.
      assert.ok(!html.includes(esc(t.privacyReview))&&!html.includes(esc(t.privacyReview.slice(0,80))),where+': the privacy review note is not printed verbatim');
      const pv=html.indexOf('class="protocol-privacy"'),privacy=pv<0?'':html.slice(pv,html.indexOf('</p>',pv));
      assert.match(privacy,label==='en'?/Only cohort aggregates are published here: no recording, no participant identifier, no per-person score\./:/这里只发布队列级聚合结果：不发布任何记录、被试编号或逐人分数。/,where+': the site-written privacy sentence');
      assert.ok(privacy.includes(`href="/data/${pj}" download`),where+': the privacy sentence links the protocol JSON');
      assert.equal(JSON.parse(readFileSync(new URL('data/'+pj,DIST),'utf8')).privacyReview,t.privacyReview,where+': the linked protocol JSON holds the full review note');
      // Beside it, the dataset's reviewed rights note from the public-data register, as the home
      // register prints it: verbatim on /, the Chinese with the released English beside it on /zh/
      // (2026-10-02 review).
      const detail=data.datasets.find(d=>d.name===t.dataset)?.detail;
      assert.ok(detail,where+': the register has a rights note for '+t.dataset);
      const rg=html.indexOf('class="protocol-register"'),register=rg<0?'':html.slice(rg,html.indexOf('</p>',rg));
      assert.ok(rg>pv,where+': the register note follows the privacy sentence');
      if(label==='en') assert.ok(register.includes('<strong>Public-data register note</strong> <span>'+esc(detail)+'</span>'),where+': the register note, verbatim');
      else assert.ok(dirZhText[detail]&&register.includes('<strong>公开数据登记说明</strong> <span>'+esc(dirZhText[detail])+'</span><span class="note-original" lang="en">'+esc(detail)+'</span>'),where+': the register note in Chinese, its English beside it');
      // The sleep protocol's review was amended for consent on 2026-09-22. The page states the caveat in
      // its own words, and every claim in them is one the released review note makes.
      if(t.id==='sleep-scalp'){
        assert.ok(privacy.includes('<span class="consent-caveat">'+consentCaveat[label]+'</span>'),where+': the consent caveat');
        for(const claim of ['publication was not mentioned in the informed consent form','the GDPR office of Region Midt judged the data fully anonymized',
                            'Consent therefore covered the study, and the public release rests on that anonymization judgment'])
          assert.ok(t.privacyReview.includes(claim),where+': the caveat rests on the released review note: '+claim);
      } else assert.doesNotMatch(privacy,/consent-caveat|Region Midt/,where+': a consent caveat without an amended review');
      // The home page's dialog says the same about privacy (its strings are a copy: the script cannot import i18n).
      const dlg=dialogs[label](t.id),dpv=dlg.indexOf('class="protocol-privacy"');
      assert.ok(dpv>0&&textOf(dlg.slice(dpv,dlg.indexOf('</p>',dpv)))===textOf(privacy),where+': the home dialog\'s privacy sentence must equal this page\'s');
      if(label==='en'){const drg=dlg.indexOf('class="protocol-register"');assert.equal(textOf(dlg.slice(drg,dlg.indexOf('</p>',drg))),textOf(register),where+': the home dialog\'s register note must equal this page\'s');}
      const fragment=t.version.match(/\{[^{}]*\}/);
      const version=fragment?t.version.replace(fragment[0],Object.entries(JSON.parse(fragment[0])).map(([k,v])=>k+' '+v).join(' · ')):t.version;
      if(fragment) assert.match(version,/ · mirror [0-9a-f]{40} · upstream \S/,where+': the fragment\'s fields, mirror then upstream');
      assert.ok(html.includes(esc(version)),where+': the dataset release, with any JSON fragment printed as its fields');
      assert.doesNotMatch(visible(html),/\{"/,where+': no JSON fragment printed raw');
      // Licence: as written; on the Chinese page, the register's Chinese with the English beside it.
      if(label==='zh'&&dirZhText[t.license]) assert.ok(html.includes('>'+esc(dirZhText[t.license])+' ↗</a><span class="note-original" lang="en">'+esc(t.license)+'</span>'),where+': the licence note in Chinese, its English beside it');
      // Compare down this table only; the lede may not claim every other protocol differs in
      // everything (beta-8ch and beta-4ch share a cohort and a chance level).
      assert.ok(html.includes(label==='en'?'other protocols differ in cohort, electrodes, window or chance level.':'其他协议在队列、电极、时间窗或随机水平上有所不同。'),where+': the results lede');
      assert.doesNotMatch(html,/other protocols have a different cohort|其他协议的队列、电极布局和随机水平都不同/,where+': the old results lede');
      // A protocol without a chance level does not promise one: not in its description,
      // social description or dek. It names the false-activation rate it is read with.
      const metas=[...html.matchAll(/<meta (?:name|property)="(?:description|og:description|twitter:description)" content="([^"]*)"/g)].map(m=>unesc(m[1]));
      const dek=(html.match(/<p class="topic-dek">([\s\S]*?)<\/p>/)||[])[1]??'';
      assert.ok(metas.length>=2&&dek.length>0,where+': description and dek render');
      if(t.chanceLevel==null) assert.ok(dek.includes(label==='en'?'and the idle false-activation rate that command detection must be read with — as the released protocol file states it.'
        :'，以及读指令检出率时必须一起看的空闲误触发率——都按已发布的协议文件给出。'),where+': the dek names the idle false-activation rate');
      for(const text of [...metas,dek]){
        if(t.chanceLevel==null){
          assert.doesNotMatch(text,label==='en'?/chance level|what guessing would score/:/随机水平|随机猜测/,where+': a protocol with no chance level promises one: '+text.slice(0,80));
          if(text!==dek) assert.match(text,label==='en'?/false-activation rate/:/误触发率/,where+': the description names the false-activation rate');
        } else if(text!==dek) assert.match(text,label==='en'?/chance level/:/随机水平/,where+': the description names the chance level');
      }
      if(t.seedSensitivity) for(const v of [...t.seedSensitivity.balancedAccuracyPercent,t.seedSensitivity.meanPercent])
        assert.ok(html.includes(`data-fig="${pj}|pct2raw|${v}"`),where+': seed result '+v);
      assert.ok(html.includes(`href="/data/${csv}"`)&&html.includes(`href="/data/${pj}"`),where+': both protocol downloads are linked');
      for(const [,href] of html.matchAll(/href="(\/[^"#]*)/g)) assert.ok(resolves(href),where+': link '+href+' does not resolve');
      // The released status field still reads "Research preview"; the site-wide check above keeps it off the page.
    }
    // Dataset markup, on the English page only: this protocol's CSV and JSON, part of the core matrix.
    const ld=JSON.parse(en.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
    assert.equal(ld['@type'],'Dataset',path+': Dataset markup');
    assert.deepEqual(ld.distribution.map(d=>d.contentUrl).sort(),[`https://bci.report/data/${csv}`,`https://bci.report/data/${pj}`,`https://bci.report/data/foundation-models-${t.id}.csv`].sort(),path+': distribution is the protocol\'s CSV and JSON, and its v9 CSV');
    assert.equal(ld.url,'https://bci.report/'+path,path+': markup url');
    assert.equal(ld.isPartOf.url,'https://bci.report/',path+': part of the core-matrix Dataset');
    assert.ok(ld.variableMeasured.includes(t.yLabel)&&ld.variableMeasured.includes(t.xLabel),path+': both metrics');
    assert.match(ld.description,t.chanceLevel==null?/false-activation rate/:/chance level/,path+': the markup describes what the protocol has');
    if(t.chanceLevel==null) assert.doesNotMatch(ld.description,/chance level/,path+': the markup promises no chance level');
    assert.ok(sitemap.includes('<loc>https://bci.report/'+path+'</loc>')&&sitemap.includes('<loc>https://bci.report/zh/'+path+'</loc>'),path+': sitemap');
    assert.ok(llms.includes('https://bci.report/'+path+'index.md'),path+': llms.txt');
    // The dataset page's group for this protocol, and every method page with a row in it, link here.
    for(const [label,prefix] of [['en',''],['zh','zh/']]){
      const inLocale=f=>label==='zh'?f.startsWith('zh/'):!f.startsWith('zh/');
      const groups=entityPages.filter(f=>inLocale(f)&&f.startsWith(prefix+'datasets/')).map(f=>readFileSync(new URL(f,DIST),'utf8')).filter(h=>h.includes(`id="g-${t.id}"`));
      assert.equal(groups.length,1,label+': exactly one dataset page carries the '+t.id+' group');
      const g=groups[0].slice(groups[0].indexOf(`id="g-${t.id}"`)),meta=g.slice(0,g.indexOf('</p>'));
      assert.ok(meta.includes(`href="/${prefix}protocols/${t.id}/"`),label+': the '+t.id+' group must link its protocol page');
      const methodGroups=entityPages.filter(f=>inLocale(f)&&f.startsWith(prefix+'methods/')).map(f=>readFileSync(new URL(f,DIST),'utf8'))
        .flatMap(h=>[...h.matchAll(new RegExp(`id="g-[a-z0-9-]+-${t.id}"[\\s\\S]*?</p>`,'g'))].map(m=>m[0]));
      assert.ok(methodGroups.length>0,label+': method pages carry '+t.id);
      for(const m of methodGroups) assert.ok(m.includes(`href="/${prefix}protocols/${t.id}/"`),label+': a method-page '+t.id+' group must link its protocol page');
    }
  }
  // No dataset or method page sends a core-matrix group to the home page any more.
  for(const f of entityPages.filter(f=>/(?:^|\/)(?:datasets|methods)\//.test(f)))
    assert.doesNotMatch(readFileSync(new URL(f,DIST),'utf8'),/Core matrix \(home page\)|核心矩阵（首页）/,f+': a core-matrix group still points at the home page');
}

console.log('PASS: protocol pages — both languages, every method with a score, every figure re-read from the protocol\'s own CSV and JSON, chance levels and the blank-cell caveat, each row equal to its CSV row, payload text verbatim except the linked privacy review and the version fields, the register\'s rights note beside the privacy sentence (and the sleep consent caveat, anchored to the review note), the home dialog saying the same, no chance level promised where there is none, Dataset markup, links resolve; entity groups and matrix headings lead here.');

// --- Model directory and data register, in Chinese -----------------------------
// mvp.json stays English (it is a released file). Its directory notes, licence
// notes and rights-review notes are translated for display only, keyed by their
// exact English text in src/data/directory-zh.json. A translation must carry
// exactly the numbers of its English (no figure typed by hand that no check
// reads), every note must have one, and no key may outlive its text.
{
  const dirZh=JSON.parse(readFileSync(new URL('../src/data/directory-zh.json',import.meta.url),'utf8')).text;
  const digits=s=>[...s.matchAll(/\d[\d,]*(?:\.\d+)?/g)].map(m=>m[0]).sort();
  for(const [en,zh] of Object.entries(dirZh)){
    assert.deepEqual(digits(zh),digits(en),'directory-zh.json: the Chinese for "'+en.slice(0,50)+'" must carry exactly its numbers');
    assert.ok(/\p{Script=Han}/u.test(zh),'directory-zh.json: "'+en.slice(0,50)+'" has no Chinese');
    for(const [bad,good] of Object.entries(rejected)) assert.ok(!hasRejected(zh,bad),`directory-zh.json: "${bad}" is a rejected rendering — use "${good}"`);
  }
  // Licence names are names: one spelling in every language.
  const licenceName=/^(?:MIT|GPL-3\.0|CC0-1\.0|CC BY 4\.0|CC BY-ND 4\.0|CC BY-NC-ND 4\.0|Open Data Commons Attribution License 1\.0)$/;
  const texts=[...data.models.flatMap(m=>[m.note,m.license]),...data.datasets.flatMap(d=>[d.detail,d.license])];
  for(const text of texts) assert.ok(dirZh[text]||licenceName.test(text),'directory-zh.json: no Chinese for "'+text.slice(0,60)+'"');
  for(const key of Object.keys(dirZh)) assert.ok(texts.includes(key),'directory-zh.json: "'+key.slice(0,50)+'" matches no text in mvp.json');
  // Since 2026-10-02 the model directory is on /methods/ and the register on /datasets/.
  const sectionOf=(html,id)=>{const a=html.indexOf(`<section id="${id}"`);assert.ok(a>0,'zh: section #'+id+' must render');return html.slice(a,html.indexOf('</section>',a));};
  const directory=sectionOf(read('zh/methods/'),'models')+sectionOf(read('zh/datasets/'),'register');
  assert.ok(directory.length>2000,'zh: the model directory and data register must render');
  assert.doesNotMatch(directory,/<p lang="en">/,'zh: every directory note has its Chinese (no untranslated fallback)');
  // Model notes print the Chinese alone. Rights-review and licence notes print the released
  // English beside the Chinese, marked lang="en" and quieter (decided 2026-10-02), on the home
  // register, the datasets index and each dataset page.
  const e=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const original=en=>'<span class="note-original" lang="en">'+e(en)+'</span>';
  for(const m of data.models){
    assert.ok(directory.includes('<p>'+e(dirZh[m.note])+'</p>')&&!directory.includes(e(m.note)),'zh: model note in Chinese alone: '+m.note.slice(0,40));
    if(dirZh[m.license]) assert.ok(directory.includes(e(dirZh[m.license])+original(m.license)),'zh: model licence note with its English: '+m.license.slice(0,40));
  }
  let originals=0;
  for(const d of data.datasets){
    assert.ok(directory.includes('<p>'+e(dirZh[d.detail])+'</p><p class="note-original" lang="en">'+e(d.detail)+'</p>'),'zh: rights-review note in Chinese with its English: '+d.detail.slice(0,40));
    originals++;
    if(dirZh[d.license]){originals++;
      assert.ok(directory.includes(e(dirZh[d.license])+(d.licenseUrl?' ↗</a>':'')+original(d.license)),'zh: dataset licence note with its English: '+d.license);}
  }
  assert.ok(originals>data.datasets.length,'zh: the register prints English originals');
  const zhIndex=read('zh/datasets/');
  // Each dataset page and its licence, as the English index lists them.
  const unq=s=>s.replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
  const datasetsWithPages=[...read('datasets/').matchAll(/<th scope="row"><a href="\/datasets\/([a-z0-9-]+)\/" lang="en">[^<]*<\/a><\/th>(?:<td>[^<]*<\/td>){3}<td>([^<]*)<\/td>/g)].map(m=>({slug:m[1],license:unq(m[2])}));
  assert.ok(datasetsWithPages.length>=16&&datasetsWithPages.some(d=>dirZh[d.license]),'datasets/: every dataset page with its licence, some of them translated');
  for(const d of datasetsWithPages) if(dirZh[d.license]){
    assert.ok(zhIndex.includes(e(dirZh[d.license])+original(d.license)),'zh/datasets/: licence note with its English: '+d.license);
    assert.ok(read('zh/datasets/'+d.slug+'/').includes(' ↗</a> <span class="note-original-inline" lang="en">('+e(d.license)+')</span>'),'zh/datasets/'+d.slug+'/: licence note with its English');
  }
  // The tightened wordings (2026-10-02).
  assert.equal(dirZh['MIT, as stated on the model card'],'MIT（据模型卡）');
  for(const [key,zh] of [['Ethics evidence is positive','伦理方面的证据是支持性的'],['materially limits privacy exposure','明显限制了隐私暴露'],['comparatively low metadata exposure','元数据暴露相对较少']]){
    const k=Object.keys(dirZh).find(x=>x.includes(key));
    assert.ok(k&&dirZh[k].includes(zh),'directory-zh.json: "'+key+'" is rendered '+zh);
  }
}
// The chart colours and the legend swatches are one list in two files (workbench.ts, generated.css).
{
  const colours=[...workbenchSource.match(/const colors=\[([^\]]+)\]/)[1].matchAll(/'(#[0-9a-fA-F]{6})'/g)].map(m=>m[1].toLowerCase());
  const swatches=[...readFileSync(new URL('../src/styles/generated.css',import.meta.url),'utf8').matchAll(/\.legend i\.s(\d+)\{background:(#[0-9a-fA-F]{6})\}/g)];
  assert.ok(colours.length>=8,'workbench.ts: the chart colours');
  assert.deepEqual(swatches.map(m=>Number(m[1])),colours.map((_,i)=>i),'generated.css: one .legend i.sN swatch per chart colour, numbered from 0');
  assert.deepEqual(swatches.map(m=>m[2].toLowerCase()),colours,'generated.css: the legend swatches must be the chart colours, in order');
  // Since 2026-10-08 (owner decision) the masthead states no date and no version: the eyebrow is the
  // site's description alone, and the release log is where dates live. The stat rail carries only the
  // core matrix's counts, under a visible caption.
  for(const [path,eyebrow] of [['','Open EEG evaluation'],['zh/','公开 EEG 评测']]){
    const html=read(path), mast=html.slice(html.indexOf('<section class="masthead">'),html.indexOf('</section>',html.indexOf('<section class="masthead">')));
    assert.ok(mast.includes(`<p class="eyebrow">${eyebrow}</p>`)&&!/<time\b/.test(mast),(path||'/')+': the masthead eyebrow carries no date');
    assert.ok(!/class="live"/.test(mast)&&/<p class="stat-caption" id="stat-caption">[^<]+<\/p><dl class="stat-rail" aria-labelledby="stat-caption">/.test(mast),(path||'/')+': the stat rail has a visible caption and no date');
  }
  // Since 2026-10-06 the lede and the stats under it count what the protocol pages carry, from the data: the core
  // matrix's protocols, datasets and methods (experiments.json; the rail keeps its four core counts, which the share
  // card prints) and the v9 matrix encoders (the export), on a line of their own under the rail. The two sets are
  // named apart and never summed. Since 2026-10-08 the lede no longer dates the encoders.
  {
    const core={protocols:data.coverage.displayedProtocols,datasets:new Set(data.tracks.map(t=>t.dataset)).size,
      comparisons:data.coverage.displayedComparisons,methods:new Set(data.tracks.flatMap(t=>t.rows.map(r=>r.name))).size};
    const v9=JSON.parse(readFileSync(new URL('data/foundation-models-update.json',DIST),'utf8'));
    const enc=v9.results['foundation-models-v9'].models.filter(m=>m.panel==='matrix').length;
    assert.ok(core.protocols===8&&core.datasets===7&&core.methods===9&&enc===13,'the masthead counts: 8 protocols, 7 datasets, 9 core methods, 13 v9 matrix encoders');
    for(const [path,zh] of [['',false],['zh/',true]]){
      const html=read(path),mast=html.slice(html.indexOf('<section class="masthead">'),html.indexOf('</section>',html.indexOf('<section class="masthead">')));
      const lede=(mast.match(/<p class="lede">([\s\S]*?)<\/p>/)||[,''])[1].replace(/&#39;/g,"'").replace(/&amp;/g,'&');
      const where=(path||'/')+': the masthead lede';
      // The Chinese lede is one sentence framed by 在……上 (review of 2026-10-06: '8 个固定协议、7 个公开数据集：协议上既有' read clipped).
      for(const s of zh?[`在 ${core.protocols} 个固定协议、${core.datasets} 个公开数据集上，既有核心矩阵的 ${core.methods} 种解码方法，也有以冻结探针方式运行的 ${enc} 个基础模型编码器。`]
                       :[`${core.protocols} fixed protocols on ${core.datasets} public datasets`,`the core matrix’s ${core.methods} decoding methods`,`and, beside them, ${enc} foundation encoders as frozen probes`])
        assert.ok(lede.includes(s),where+' says "'+s+'", counted from the data');
      assert.ok(!/公开数据集：协议上/.test(lede),where+': not the clipped "……公开数据集：协议上既有" opening');
      assert.ok(!new RegExp('(^|\\D)'+(core.methods+enc)+'(\\D|$)').test(lede),where+': no summed count of core methods and v9 encoders');
      assert.deepEqual([...mast.matchAll(/<dd>(\d+)<\/dd>/g)].map(m=>Number(m[1])),[core.protocols,core.datasets,core.comparisons,core.methods],(path||'/')+': the stat rail is the core matrix\'s four counts, in order');
      const added=mast.match(/<\/dl>\s*<p class="stat-added">([\s\S]*?)<\/p>/);
      assert.ok(added&&added[1].includes(`<span data-count="encoders">${enc}</span>`)&&added[1].includes(`href="${zh?'/zh':''}/protocols/"`)&&!/v9|第九轮/.test(added[1]),
        (path||'/')+': the line under the rail counts the v9 matrix encoders ('+enc+') and links the protocols');
      // It sits under 'Methods 9': no leading '+', which invited reading 9 + 13 (review of 2026-10-06).
      const addedText=added?added[1].replace(/<[^>]+>/g,'').replace(/&#43;|&plus;/g,'+').replace(/&amp;/g,'&').trim():'';
      assert.ok(!/^[+＋]/.test(addedText),(path||'/')+': the line under the rail must not open with "+", which reads as a sum with the methods above it');
      assert.equal(addedText,zh?`另有 ${enc} 个基础模型编码器在同样的协议上（冻结）→`:`Also on these protocols: ${enc} foundation encoders, frozen →`,(path||'/')+': the line under the rail');
    }
  }
}

// --- 2026-10-02 discoverability and citation ---------------------------------------------
const decodeHtml=s=>s.replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
const sha256=u=>createHash('sha256').update(readFileSync(u)).digest('hex');
const siteTs=readFileSync(new URL('../src/data/site.ts',import.meta.url),'utf8');
const siteField=k=>siteTs.match(new RegExp('^\\s*'+k+":\\s*'([^']+)'",'m'))[1];
const [repository,mirror,citationFile]=['repository','mirror','citationFile'].map(siteField);
const ldOf=html=>[...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(m=>JSON.parse(m[1]));
const releasesPage=pageOf('releases/');
const releaseEntries=[...releasesPage.matchAll(/<article class="release-entry" id="([^"]+)">\s*<header><time datetime="([^"]+)">([\s\S]*?)<\/article>/g)]
  .map(m=>({id:m[1],date:m[2],files:[...m[3].matchAll(/data-file="([^"]+)"/g)].map(f=>f[1])}));
assert.ok(releaseEntries.length>=6,'the releases page must list every release');
const releaseOf=new Map(releaseEntries.flatMap(r=>r.files.map(f=>[f,r])));
const [newestRelease,oldestRelease]=[releaseEntries[0],releaseEntries.at(-1)];

// The share card. A text check cannot see inside a bitmap, which is how og.png kept
// the "Research preview" badge after the pages dropped it; the generator records
// the hash, size, text and counts of what it drew, and the served file must be that.
{
  const brand=JSON.parse(readFileSync(new URL('./brand-assets.json',import.meta.url),'utf8'));
  const card=brand['og.png'];
  for(const [file,{sha256:want}] of Object.entries(brand)){
    assert.equal(sha256(new URL('../public/'+file,import.meta.url)),want,'public/'+file+' is not the file generate-brand-assets.py recorded');
    assert.equal(sha256(new URL(file,DIST)),want,'dist/'+file+' is not the recorded file');
  }
  assert.notEqual(card.sha256,'cffe4021be4c624f63afcec7ee8222b004d9b4a89f020241121d2bf5bff149d5','the share card with the "Research preview" badge is back');
  assert.ok(card.text.every(s=>!/preview|研究预览/i.test(s)),'the share card must not carry a stage label');
  const png=readFileSync(new URL('og.png',DIST));
  assert.deepEqual([png.readUInt32BE(16),png.readUInt32BE(20)],[card.width,card.height],'og.png must be the size the pages declare');
  const core={protocols:data.coverage.displayedProtocols,datasets:new Set(data.tracks.map(t=>t.dataset)).size,
    comparisons:data.coverage.displayedComparisons,methods:new Set(data.tracks.flatMap(t=>t.rows.map(r=>r.name))).size};
  assert.deepEqual(card.counts,core,'the share card prints counts that are not the core matrix\'s: regenerate og.png');
  for(const f of [...htmlPages,'404.html'].filter(f=>readFileSync(new URL(f,DIST),'utf8').includes('property="og:image"'))){
    const html=readFileSync(new URL(f,DIST),'utf8');
    for(const tag of ['og:image:type" content="image/png"','og:image:width" content="'+card.width+'"','og:image:height" content="'+card.height+'"'])
      assert.ok(html.includes('<meta property="'+tag+'>'),f+': '+tag.split('"')[0]+' is required beside og:image');
    const alt=decodeHtml(html.match(/<meta property="og:image:alt" content="([^"]+)"/)?.[1]??'');
    assert.ok(alt.includes(String(core.comparisons))&&alt.includes(String(core.protocols)),f+': og:image:alt must describe the card');
    if(/<html lang="en"/.test(html)) assert.ok(alt.includes(card.text[1]+' '+card.text[2]),f+': the English alt text quotes the card');
    assert.ok(html.includes('<meta name="twitter:image:alt" content="'),f+': twitter:image:alt is required');
  }
}

// The umbrella Dataset on the home page cites what CITATION.cff and /api/ cite: the
// newest release, with every file any release ships, and the topic datasets as parts.
{
  const ld=ldOf(built);
  const umbrella=ld.find(x=>x['@type']==='Dataset'),website=ld.find(x=>x['@type']==='WebSite');
  assert.equal(umbrella.version,newestRelease.id,'home Dataset version must be the newest release');
  assert.equal(umbrella.dateModified,newestRelease.date,'home Dataset dateModified must be the newest release date');
  assert.equal(umbrella.datePublished,oldestRelease.date,'home Dataset datePublished must be the first release date');
  assert.deepEqual(umbrella.distribution.map(d=>d.contentUrl.replace('https://bci.report/data/','')).sort(),
    readdirSync(new URL('data/',DIST)).sort(),'home Dataset distribution must name every served file');
  assert.deepEqual(umbrella.hasPart.map(p=>p.url).sort(),topicPages.map(([s])=>'https://bci.report/topics/'+s+'/').sort(),'home Dataset hasPart must name every topic Dataset');
  for(const part of umbrella.hasPart){
    const node=ldOf(pageOf(part.url.replace('https://bci.report/','')))[0]['@graph'].find(n=>n['@type']==='Dataset');
    assert.equal(part.name,node.name,part.url+': hasPart must name the topic Dataset as the topic page does');
  }
  // model-adaptation prints the adapter's parameter counts from the 2026-09-22 engineering check, so
  // that file is in its distribution (and its cite block); a parameter count measures nothing, so
  // variableMeasured names the adaptation metrics only (2026-10-02 review).
  {
    const node=ldOf(pageOf('topics/model-adaptation/'))[0]['@graph'].find(n=>n['@type']==='Dataset');
    assert.ok(node.distribution.some(d=>d.contentUrl==='https://bci.report/data/evidence-update.json'),'model-adaptation: the engineering check\'s file stays in distribution');
    assert.deepEqual(node.variableMeasured,['balanced_accuracy','macro_f1'],'model-adaptation: variableMeasured names what was measured, not the adapter\'s size');
  }
  assert.deepEqual([...umbrella.sameAs].sort(),[mirror,repository].sort(),'home Dataset sameAs: the mirror and the repository');
  // The topic batches inform those questions; they do not settle them.
  assert.ok(umbrella.description.includes(`Separately reviewed batches bear on ${topicPages.length} deployment questions`),'home Dataset: the batches bear on the deployment questions');
  assert.doesNotMatch(umbrella.description,/\banswer \d+ deployment questions/,'home Dataset: the batches do not answer the questions');
  assert.deepEqual([...website.sameAs].sort(),[mirror,repository].sort(),'WebSite sameAs: the repository and the mirror');
  for(const f of htmlPages) for(const node of ldOf(readFileSync(new URL(f,DIST),'utf8')))
    assert.ok(!JSON.stringify(node).includes('"@type":"Person"'),f+': BCI Report is a project byline, an Organization, not a Person');
}

// The release feed: one entry per release in the releases page's order, every file
// with its served size and SHA-256, linked from every page's head and from /api/.
{
  const feed=readFileSync(new URL('releases.xml',DIST),'utf8');
  assert.match(feed,/^<\?xml version="1\.0" encoding="utf-8"\?>\n<feed xmlns="http:\/\/www\.w3\.org\/2005\/Atom" xml:lang="en">/,'releases.xml is an Atom feed');
  assert.equal((feed.match(/<entry>/g)||[]).length,(feed.match(/<\/entry>/g)||[]).length);
  assert.deepEqual([...feed.matchAll(/<entry>\n {4}<title>[^<]*<\/title>\n {4}<id>https:\/\/bci\.report\/releases\/#([^<]+)<\/id>/g)].map(m=>m[1]),
    releaseEntries.map(r=>r.id),'releases.xml: one entry per release, newest first');
  assert.ok(feed.includes('<updated>'+newestRelease.date+'T00:00:00Z</updated>\n  <author>'),'releases.xml: the feed is as new as the newest release');
  for(const r of releaseEntries) for(const file of r.files){
    const bytes=readFileSync(new URL('data/'+file,DIST));
    assert.ok(feed.includes(`length="${bytes.length}" href="https://bci.report/data/${file}"`),'releases.xml: '+file+' enclosure must carry its served size');
    // Named as the releases page names it: the hash of the file as served.
    assert.ok(feed.includes(`SHA-256 of the file as served &lt;code&gt;${createHash('sha256').update(bytes).digest('hex')}&lt;/code&gt;`),'releases.xml: '+file+' must carry the SHA-256 of the served bytes');
  }
  for(const f of htmlPages){
    const html=readFileSync(new URL(f,DIST),'utf8');
    assert.ok(html.includes('<link rel="alternate" type="application/atom+xml" title="BCI Report releases" href="/releases.xml">'),f+': the release feed must be linked in <head>');
  }
  for(const p of ['api/','zh/api/']){
    const html=pageOf(p);
    for(const href of ['/releases.xml','/llms-full.txt','/llms.txt','/sitemap.xml']) assert.ok(html.includes(`href="${href}"`),p+': '+href+' must be linked for agents');
    // From the Chinese page, a link to an English-only file says so (the sitemap lists both languages).
    if(p==='zh/api/') for(const href of ['/llms.txt','/llms-full.txt','/releases.xml'])
      assert.ok(html.includes(`<a href="${href}"><code>${href}</code></a>（英文）——`),p+': '+href+' is English only and must say so');
    if(p==='zh/api/') assert.ok(html.includes('<a href="/sitemap.xml"><code>/sitemap.xml</code></a>——'),p+': the sitemap lists both languages and carries no English mark');
    for(const href of [repository,mirror,citationFile]) assert.ok(html.includes(`href="${href}"`),p+': '+href+' must be linked');
    // Since 2026-10-05 the edge lets any client read /data/, the llms files and the Markdown
    // copies (a Cloudflare configuration rule), so the page says so instead of the old caveat.
    assert.match(html,p==='api/'?/Any HTTP client can fetch the files under \/data\/, the llms files and the Markdown copies/:/\/data\/ 下的文件、llms 文件和各页的 Markdown 副本，任何 HTTP 客户端都能下载/,p+': the page says which files any client can fetch');
  }
}

// _headers: the downloads may be read from any origin; the pages may not.
{
  const blocks={};let current=null;
  for(const line of headers.split('\n')){
    if(!line.trim()||/^\s*#/.test(line)) continue;
    if(/^\S/.test(line)){current=line.trim();blocks[current]=[];} else blocks[current].push(line.trim());
  }
  assert.deepEqual(blocks['/data/*'],['! Cross-Origin-Resource-Policy','Cross-Origin-Resource-Policy: cross-origin','Access-Control-Allow-Origin: *'],
    '/data/* must detach the same-origin policy, then allow cross-origin reads');
  assert.ok(blocks['/*'].includes('Cross-Origin-Resource-Policy: same-origin'),'pages keep Cross-Origin-Resource-Policy: same-origin');
  for(const [path,lines] of Object.entries(blocks)) if(path!=='/data/*')
    assert.ok(!lines.some(l=>/^Access-Control-Allow-Origin|^Cross-Origin-Resource-Policy: cross-origin/.test(l)),path+': only /data/* is readable cross-origin');
  assert.deepEqual(blocks['/releases.xml'],['Content-Type: application/atom+xml; charset=utf-8'],'the feed is served as Atom');
  assert.equal(readFileSync(new URL('_headers',DIST),'utf8'),headers,'dist/_headers must be public/_headers');
}

// "Cite this page" on every topic, dataset and method page, in both languages and
// in each Markdown copy: the page, its address, and exactly the releases whose
// files hold its figures (topic pages: the downloads they link, and since
// 2026-10-02 the files of any data-fig figure they print; entity pages: the files
// their data-fig figures are leaves of). citation_* tags carry the same.
{
  // Since 2026-10-04 the protocol pages too: they print the core release's rows and the v9 rows.
  const citePages=[...topicPages.map(([s])=>'topics/'+s+'/'),...entityBilingual.filter(p=>/^(?:datasets|methods|protocols)\/[^/]+\/$/.test(p))];
  assert.ok(citePages.length>=9+16+9,'cite blocks on every topic, dataset and method page');
  for(const p of citePages) for(const path of [p,'zh/'+p]){
    const html=pageOf(path),zh=path.startsWith('zh/');
    const start=html.indexOf('<section class="cite-page"');
    assert.ok(start>0,path+': the cite block must render');
    const sec=html.slice(start,html.indexOf('</section>',start));
    const named=sec.match(/data-releases="([^"]+)"/)[1].split(' ');
    const figFiles=[...html.matchAll(/data-fig="([^|"]+)\|/g)].map(m=>m[1]);
    const files=p.startsWith('topics/')?[...[...html.matchAll(/href="\/data\/([^"]+)"/g)].map(m=>m[1]),...figFiles]:figFiles;
    const expected=releaseEntries.filter(r=>files.some(f=>releaseOf.get(f)===r)).map(r=>r.id);
    assert.deepEqual(named,expected,path+': the cite block must name exactly the releases its figures come from, newest first');
    for(const id of named) assert.ok(sec.includes(`href="${zh?'/zh':''}/releases/#${id}"><code>${id}</code></a>`),path+': '+id+' must link to its release');
    // The h1 may carry markup (an English name in <span lang="en">, <wbr> phrase breaks); the cite block names its text.
    const h1=html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/)[1].replace(/<[^>]+>/g,''),canonical='https://bci.report/'+path;
    assert.ok(sec.includes(`<cite>${h1}</cite>`)&&sec.includes(`<span class="cite-url">${canonical}</span>`),path+': the cite block names the page and its address');
    assert.match(sec,zh?/也请同时引用上游数据集/:/Cite the upstream datasets? as well/,path+': the cite block sends the reader to the upstream credit');
    // Plural on topic pages, which draw on several datasets; singular on a dataset's own page
    // (2026-10-02 review); method pages send the reader to the dataset pages.
    const upstream=p.startsWith('methods/')?(zh?'也请同时引用上游数据集：每个数据集页面都写明了署名。':'Cite the upstream datasets as well: each dataset’s page gives its credit.')
      :/^(?:datasets|protocols)\//.test(p)?(zh?'也请同时引用上游数据集：其署名就在本页。':'Cite the upstream dataset as well: its credit is on this page.')
      :(zh?'也请同时引用上游数据集：署名就在本页。':'Cite the upstream datasets as well: their credits are on this page.');
    assert.ok(sec.includes(upstream),path+': the upstream credit sentence: '+upstream);
    const newest=releaseEntries.find(r=>r.id===named[0]);
    const meta=k=>decodeHtml(html.match(new RegExp(`<meta name="citation_${k}" content="([^"]*)">`))?.[1]??'');
    assert.equal(meta('title'),decodeHtml(h1),path+': citation_title is the h1');
    // No citation_author: Zotero parses "BCI Report" as a person, "Report, B.". The project is the publisher.
    assert.doesNotMatch(html,/<meta name="citation_author"/,path+': no citation_author');
    assert.equal(meta('publisher'),'BCI Report',path+': citation_publisher');
    assert.equal(meta('publication_date'),newest.date.replaceAll('-','/'),path+': citation_publication_date is the newest cited release');
    assert.equal(meta('public_url'),canonical,path+': citation_public_url is the canonical');
    const md=readFileSync(new URL(path+'index.md',DIST),'utf8');
    assert.ok(md.includes(zh?'## 引用本页':'## Cite this page')&&named.every(id=>md.includes('`'+id+'`'))&&md.includes(canonical),path+': the cite block must survive into the Markdown copy');
  }
}

// A topic page that prints a figure from a file other than its own exports marks
// it as the entity pages do (data-fig, Fig.astro). Re-read every such figure from
// the served file; the cite block above already has to name its release.
// The core matrix's frozen LaBraM readout is the case that prompted this: printed
// for scale on model-adaptation (calibration-budget until 2026-10-02) without
// experiments.json among the page's links, so the cite block named no core release.
{
  const matrixMark=`data-fig="experiments.json|pct1raw|${matrixLabram.y}">${matrixLabram.y.toFixed(1)}%<`;
  const matrixSentence=/core matrix's frozen LaBraM|核心矩阵中[^。]*冻结 LaBraM/;
  let topicFigs=0,printedMatrix=0;
  for(const [slug] of topicPages) for(const path of ['topics/'+slug+'/','zh/topics/'+slug+'/']){
    const html=pageOf(path);
    for(const [,file,format,raw,text] of html.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)){
      assert.ok(leavesOf(file).has(Number(raw)),path+': '+raw+' is not a value in '+file);
      assert.equal(text,fmt[format](Number(raw)),path+': '+file+' '+raw+' printed as "'+text+'"');
      topicFigs++;
    }
    // A topic that names the matrix LaBraM readout prints it marked. Since 2026-10-04 other topics print other
    // released rows from experiments.json too (the v9 sections read new rows against them), so that file alone
    // no longer implies the readout; any experiments.json figure still requires the core release in the cite block.
    if(matrixSentence.test(visible(html))){
      printedMatrix++;
      assert.ok(html.includes(matrixMark),path+': the matrix LaBraM readout must be printed from experiments.json, marked');
    }
    if(matrixSentence.test(visible(html))||html.includes('data-fig="experiments.json|')){
      const cite=html.slice(html.indexOf('<section class="cite-page"'));
      assert.ok(cite.match(/data-releases="([^"]+)"/)[1].split(' ').includes(data.releaseId),path+': prints a released matrix row, so its cite block must name '+data.releaseId);
    }
  }
  assert.ok(topicFigs>=2*5,'model-adaptation marks the matrix readout and the adapter counts ('+topicFigs+')');
  assert.ok(pageOf('topics/model-adaptation/').includes(matrixMark)&&pageOf('zh/topics/model-adaptation/').includes(matrixMark)&&printedMatrix>=2,'model-adaptation prints the matrix readout in both languages');
}

// Topic → entity links (2026-10-02). Entity pages linked back to topics; no topic
// linked to a dataset or method page, so seven datasets had one real inbound link.
// Every topic now carries a "Measured on … · Methods …" line under its hero, derived
// from the entity groups (entities.ts, topicEntities). Checked here from the built
// pages: the line links exactly the dataset and method pages whose result groups
// point at that topic — none missing, none extra — in both languages and the
// Markdown copy.
{
  for(const [label,prefix] of [['en',''],['zh','zh/']]){
    const pointing=new Map(topicPages.map(([s])=>[s,new Set()]));
    // Core-matrix rows a topic prints reach it through their protocol page, not a group link
    // (2026-10-02): when-not-to-act prints the whole idle table, model-adaptation the frozen
    // LaBraM readout on arithmetic-rest. Kept here independently of entities.ts, and each is
    // confirmed against the topic page itself below.
    const protocolRead={'when-not-to-act':{track:'idle'},'model-adaptation':{track:'arithmetic-rest',method:'labram'}};
    for(const f of entityPages.filter(f=>(label==='zh')===f.startsWith('zh/')&&/(?:^|\/)(?:datasets|methods)\/[^/]+\/index\.html$/.test(f))){
      const self='/'+f.replace(/index\.html$/,''),text=readFileSync(new URL(f,DIST),'utf8');
      for(const [,slug] of text.matchAll(/<p class="entity-group-meta">[^<]*<a href="\/(?:zh\/)?topics\/([^/"#]+)\//g)){
        assert.ok(pointing.has(slug),f+': a result group points at '+slug+', which is not a topic page');
        pointing.get(slug).add(self);
      }
      // A core-matrix group links its protocol page bare; a v9 group links the page's v9 section (#foundation-v9),
      // which no topic prints through, so only bare links count here.
      for(const [,track] of text.matchAll(/<p class="entity-group-meta">[^<]*<a href="\/(?:zh\/)?protocols\/([^/"#]+)\/"/g))
        for(const [slug,r] of Object.entries(protocolRead))
          if(r.track===track&&(!r.method||!/(?:^|\/)methods\//.test(f)||self.endsWith('/methods/'+r.method+'/'))) pointing.get(slug).add(self);
    }
    // Since 2026-10-04 the v9 sections print released and new rows through their protocol pages (does-pretraining-help,
    // fewer-electrodes). Read from the topic page itself, not from entities.ts: every such row carries
    // data-core-topic="<track>|<row id>" or data-fm-topic="<track>|<checkpoint>", and the v9 topics block below holds
    // every figure there to an attribute naming its file's protocol. A printed row adds its dataset's page and its
    // method's page (a released row whose method has none, spectral ridge, adds only the dataset's).
    {
      const MVPS={ds003810:'ds003810',EEGMAT:'eegmat','EESM19 scalp subset':'eesm19',BETA:'beta','TMNRED / ds005383':'tmnred',ds006593:'ds006593',ds005342:'ds005342'};
      const CORE_PAGE={eegnet:'eegnet',labram:'labram',cbramod:'cbramod',cca:'cca','csp-lda':'csp-lda',shallowfbcspnet:'shallowfbcspnet',deep4net:'deep4net',fbcca:'fbcca','ensemble-trca':'etrca'};
      const FMS=JSON.parse(readFileSync(new URL('data/foundation-models-update.json',DIST),'utf8')).results['foundation-models-v9'];
      const FAMILY=id=>({'reve-base':'reve','reve-large':'reve','luna-base':'luna','luna-large':'luna','brainomni-base':'brainomni','steegformer-base':'st-eegformer',
        'steegformer-large':'st-eegformer','erp-fm-base':'erp-fm'})[id]??(id.startsWith('eeg-fm-masking/')?'eeg-fm-masking':id);
      for(const [slug] of topicPages){
        const html=pageOf(prefix+'topics/'+slug+'/');
        for(const [,kind,track,id] of html.matchAll(/data-(core|fm)-topic="([^"|]+)\|([^"]+)"/g)){
          const t=data.tracks.find(x=>x.id===track);
          assert.ok(t,slug+': a printed row names '+track+', which is not a core protocol');
          pointing.get(slug).add('/'+prefix+'datasets/'+MVPS[t.dataset]+'/');
          if(kind==='core'){assert.ok(t.rows.some(r=>r.id===id),slug+': '+track+' has no released row '+id);if(CORE_PAGE[id])pointing.get(slug).add('/'+prefix+'methods/'+CORE_PAGE[id]+'/');}
          else {assert.ok(FMS.models.some(m=>m.id===id),slug+': no v9 checkpoint '+id);pointing.get(slug).add('/'+prefix+'methods/'+FAMILY(id)+'/');}
        }
      }
    }
    // The protocol rows really are printed: every idle method on when-not-to-act, the marked readout on model-adaptation.
    {const w=pageOf(prefix+'topics/when-not-to-act/'),a=w.indexOf('<table'),idleTable=w.slice(a,w.indexOf('</table>',a));
     assert.match(w.slice(w.lastIndexOf('aria-label="',a),a),/Idle and command|空闲/,prefix+'topics/when-not-to-act/: its first table is the idle table');
     for(const m of data.tracks.find(t=>t.id==='idle').rows) assert.ok(visible(idleTable).includes(m.name),prefix+'topics/when-not-to-act/: the idle table prints the row of '+m.name);}
    assert.ok(pageOf(prefix+'topics/model-adaptation/').includes('data-fig="experiments.json|'),prefix+'topics/model-adaptation/: prints the matrix readout');
    for(const [slug,pages] of pointing){
      const path=prefix+'topics/'+slug+'/',html=pageOf(path);
      const at=html.indexOf('<p class="topic-entities">');
      assert.ok(pages.size>0,path+': no dataset or method page points here');
      assert.ok(at>html.indexOf('class="topic-hero"')&&at<html.indexOf('class="short-answer"'),path+': the Measured on line sits under the hero, before the short answer');
      const line=html.slice(at,html.indexOf('</p>',at));
      const linked=[...line.matchAll(/href="([^"]+)"/g)].map(m=>m[1]);
      assert.deepEqual([...linked].sort(),[...pages].sort(),path+': the Measured on line must link exactly the dataset and method pages whose groups point here, plus the protocol rows it prints');
      assert.match(line,label==='zh'?/测量所用数据集：/:/Measured on:/,path+': the line says what it lists');
      const md=readFileSync(new URL(path+'index.md',DIST),'utf8');
      for(const p of pages) assert.ok(md.includes('](https://bci.report'+p+')'),path+'index.md: the Measured on line must survive into the Markdown copy ('+p+')');
    }
  }
}

// Markdown copies keep the names that live in table controls: the home matrix heads
// its columns with '#' links and names each model in a button. Skipping them as
// navigation left the copy's tables with no labels (fixed 2026-10-02).
for(const f of htmlPages){
  const html=readFileSync(new URL(f,DIST),'utf8'),copy=readFileSync(new URL(f.replace(/index\.html$/,'index.md'),DIST),'utf8');
  const rows=copy.split('\n').filter(l=>l.startsWith('| '));
  for(const [table] of html.matchAll(/<table[\s\S]*?<\/table>/g))
    for(const [,label] of table.matchAll(/<(?:button|a href="#[^"]*")[^>]*>([^<]+)</g)){
      const text=decodeHtml(label).replace(/\s*↗\s*$/,'').trim();
      if(text) assert.ok(rows.some(l=>l.includes(text)),f+': "'+text+'" names a table row or column and must be in the Markdown table');
    }
}
for(const [path,names] of [['index.md',data.tracks.map(t=>t.title)],['zh/index.md',null]]){
  const head=readFileSync(new URL(path,DIST),'utf8').split('\n').find(l=>/^\| (?:Method|方法) \|/.test(l));
  assert.ok(head&&head.split('|').slice(2,-1).every(c=>/\S+ — n=/.test(c)),path+': every matrix column must keep its protocol name');
  if(names) for(const n of names) assert.ok(head.includes(n),path+': matrix column '+n);
}

// Titles say the site's name once.
for(const f of htmlPages){
  const title=readFileSync(new URL(f,DIST),'utf8').match(/<title>([^<]*)<\/title>/)[1];
  assert.ok(title.split('BCI Report').length<=2,f+': "'+title+'" repeats the site name');
}

// The project's other homes: every footer links back to them, the agent files list them.
for(const f of htmlPages){
  const html=readFileSync(new URL(f,DIST),'utf8');
  const footer=html.slice(html.lastIndexOf('<footer'));
  for(const href of [repository,mirror,citationFile]) assert.ok(footer.includes(`href="${href}"`),f+': the footer must link '+href);
  // They open in a new tab, and say so with the ↗ every other such link carries.
  for(const [,attrs,label] of footer.slice(footer.indexOf('footer-elsewhere')).matchAll(/<a ([^>]*)>([^<]*)<\/a>/g))
    if(/target="_blank"/.test(attrs)) assert.match(label,/ ↗(?:（英文）)?$/,f+': footer link "'+label+'" opens a new tab without the ↗ cue');
}
assert.match(llms,/\n## Cite\n\n[\s\S]*\n## Mirrors\n\n[\s\S]*\n## Optional\n/,'llms.txt: Cite and Mirrors sections, before Optional');
assert.ok(llms.includes('`'+newestRelease.id+'`'),'llms.txt must cite the newest release');
for(const url of [repository,mirror,citationFile,'https://bci.report/releases.xml','https://bci.report/llms-full.txt'])
  assert.ok(llms.includes(`](${url})`),'llms.txt must link '+url);
// Unmeasured models can be linked by name; their entries carry no number.
{
  const methodsPage=pageOf('methods/');
  const list=methodsPage.slice(methodsPage.indexOf('id="unmeasured"'),methodsPage.indexOf('</ul>',methodsPage.indexOf('id="unmeasured"')));
  const items=[...list.matchAll(/<li( id="[a-z0-9-]+")?>/g)];
  assert.ok(items.length>0&&items.every(m=>m[1]),'methods: every unmeasured model has an anchor');
  assert.doesNotMatch(list.replace(/<[^>]+>/g,' '),/\d+(?:\.\d+)?\s?%/,'methods: an unmeasured model carries no figure');
}

// Licences and archive metadata: code MIT, the aggregate results CC BY 4.0, and the
// Zenodo record derived from CITATION.cff and the built dataset pages.
{
  const repoFile=f=>readFileSync(new URL('../../'+f,import.meta.url),'utf8');
  assert.match(repoFile('LICENSE'),/^MIT License\n\nCopyright \(c\) \d{4} /,'LICENSE: the code is MIT');
  const dataLicence=repoFile('LICENSE-DATA');
  assert.ok(dataLicence.includes('https://creativecommons.org/licenses/by/4.0/')&&dataLicence.includes('site/public/data/'),'LICENSE-DATA: CC BY 4.0, scoped to the published aggregate files');
  assert.match(dataLicence,/does not cover[\s\S]*EEG recordings/,'LICENSE-DATA: the recordings keep their own terms');
  const cff=repoFile('CITATION.cff');
  assert.match(cff,/^license: CC-BY-4\.0$/m,'CITATION.cff: the dataset licence');
  assert.match(cff,/MIT License \(LICENSE\)/,'CITATION.cff: the code licence is stated');
  const readme=repoFile('README.md');
  assert.ok(readme.includes('[LICENSE-DATA](LICENSE-DATA)')&&readme.includes('[MIT](LICENSE)'),'README: both licences are linked');
  const zenodo=JSON.parse(repoFile('.zenodo.json'));
  const {zenodoMetadata}=await import('./write-zenodo-metadata.mjs');
  assert.deepEqual(zenodo,zenodoMetadata(DIST),'.zenodo.json is stale: run `node scripts/write-zenodo-metadata.mjs` after the build');
  assert.equal(zenodo.upload_type,'dataset');
  assert.equal(zenodo.license,'cc-by-4.0');
  assert.deepEqual(zenodo.creators,[{name:'BCI Report'}]);
  for(const h of held) assert.ok(!JSON.stringify(zenodo).includes(h.name)&&!JSON.stringify(zenodo).includes(h.source.split('/').pop()),'.zenodo.json: held source '+h.id+' appears');
  // The /api/ BibTeX is the citation CITATION.cff gives.
  const bib=decodeHtml(apiPage.match(/<pre class="code" lang="en"><code>(@misc[\s\S]*?)<\/code><\/pre>/)[1]);
  const cffField=k=>cff.match(new RegExp('^'+k+': "?([^"\\n]+)"?$','m'))[1];
  assert.ok(bib.includes(`title        = {${cffField('title')}}`)&&bib.includes(`note         = {Release ${cffField('version')}}`)&&bib.includes(`year         = {${cffField('date-released').slice(0,4)}}`),
    'the /api/ BibTeX must be the citation CITATION.cff gives');
  // The Zenodo concept DOI (site.ts `archive`) is the one CITATION.cff, the BibTeX, the home Dataset,
  // llms.txt and every cite block carry (archive connected 2026-10-03).
  const conceptDoi=readFileSync(new URL('../src/data/site.ts',import.meta.url),'utf8').match(/conceptDoi: '(10\.5281\/zenodo\.\d+)'/)[1];
  assert.equal(cffField('doi'),conceptDoi,'CITATION.cff: doi is the Zenodo concept DOI');
  assert.ok(bib.includes(`doi          = {${conceptDoi}}`),'the /api/ BibTeX carries the concept DOI');
  assert.equal(ldOf(built).find(x=>x['@type']==='Dataset').identifier,'https://doi.org/'+conceptDoi,'home Dataset identifier is the concept DOI');
  assert.ok(readFileSync(new URL('llms.txt',DIST),'utf8').includes('DOI '+conceptDoi),'llms.txt names the concept DOI');
  assert.ok(repoFile('README.md').includes('https://doi.org/'+conceptDoi),'README: the DOI badge');
  for(const p of ['topics/dry-vs-wet/','zh/datasets/ltrsvp/','methods/labram/']){
    const html=pageOf(p),cite=html.slice(html.indexOf('<section class="cite-page"'));
    assert.ok(cite.includes(`<a href="https://doi.org/${conceptDoi}">doi:${conceptDoi}</a>`),p+': the cite block links the archive DOI');
  }
}

// --- 2026-10-02 home, navigation and the Questions hub -------------------------------------
// The home page was restructured: questions grouped, a compact transfer-coverage map, holds that
// link, the core matrix with its snapshot date, a directory band. The model directory and field
// notes moved to /methods/, the public-data register to /datasets/. /topics/ is the Questions hub.
{
  const releasesHtml=pageOf('releases/');
  // Navigation: the same eight entries, in order, on every page of a language; the current one marked.
  const navOf=html=>{const m=html.match(/<nav aria-label="(?:Main navigation|主导航)">([\s\S]*?)<\/nav>/);assert.ok(m,'the main navigation must render');return [...m[1].matchAll(/<a href="([^"]+)"(?: aria-current="page")?>([^<]+)<\/a>/g)].map(x=>[x[1],x[2]]);};
  const navWant={en:[['/topics/','Questions'],['/#overview','Results'],['/protocols/','Protocols'],['/methods/','Methods'],['/datasets/','Datasets'],['/releases/','Releases'],['/api/','API'],['/data-use/','Data use']],
                 zh:[['/zh/topics/','问题'],['/zh/#overview','结果'],['/zh/protocols/','协议'],['/zh/methods/','方法'],['/zh/datasets/','数据集'],['/zh/releases/','发布记录'],['/zh/api/','API'],['/data-use/','数据使用（英文）']]};
  for(const f of htmlPages.filter(f=>f!=='404.html'&&!/^data-use\//.test(f))){
    const html=readFileSync(new URL(f,DIST),'utf8');
    const home=f==='index.html'||f==='zh/index.html';   // on the home page itself Results is an in-page link
    assert.deepEqual(navOf(html),navWant[f.startsWith('zh/')?'zh':'en'].map(([h,l])=>[home&&/#overview$/.test(h)?'#overview':h,l]),f+': the main navigation');
  }
  for(const [page,href] of [['api/','/api/'],['zh/api/','/zh/api/'],['topics/','/topics/'],['zh/topics/','/zh/topics/'],['methods/','/methods/'],['zh/datasets/','/zh/datasets/']])
    assert.ok(pageOf(page).includes(`<a href="${href}" aria-current="page">`),page+': its own entry is marked current');
  // Breadcrumbs: Questions is the middle crumb of every topic page, and topic and entity pages emit BreadcrumbList.
  for(const [s] of topicPages) for(const [p,hub] of [['topics/'+s+'/','/topics/'],['zh/topics/'+s+'/','/zh/topics/']]){
    const html=pageOf(p);
    assert.ok(html.includes(`<nav class="breadcrumbs"`)&&html.includes(`<li><a href="${hub}">`),p+': the breadcrumb passes through the Questions hub');
    // Structured data sits on the English canonical only (one entity per resource; hreflang joins the two).
    if(!p.startsWith('zh/')) assert.ok(html.includes('"@type":"BreadcrumbList"')&&html.includes('"item":"https://bci.report'+hub+'"'),p+': BreadcrumbList names the hub');
  }
  for(const f of entityPages.filter(f=>!f.startsWith('zh/'))) assert.ok(readFileSync(new URL(f,DIST),'utf8').includes('"@type":"BreadcrumbList"'),f+': BreadcrumbList');
  // The Questions hub and the home page list every topic once, under the three groups, in both languages.
  for(const page of ['','topics/','zh/','zh/topics/']){
    const html=pageOf(page);
    for(const g of ['transfer','adapting','reliability']) assert.ok(html.includes(`id="group-${g}"`),(page||'/')+': group '+g);
    const cards=[...html.matchAll(/<a class="topic-entry-card" href="(?:\/zh)?\/topics\/([^/]+)\/"/g)].map(m=>m[1]);
    assert.deepEqual([...cards].sort(),topicPages.map(([s])=>s).sort(),(page||'/')+': every topic card exactly once');
  }
  // Topic-card counts: every number a card prints is a cohort size or design figure from its own payload.
  const ysuX=xt.results['ysu-async-ssvep-extension'],ltr=xt.results['ltrsvp-rate-transfer'];
  const lsx=JSON.parse(readFileSync(new URL('../src/data/large-source-update.json',import.meta.url),'utf8'));
  const fmCard=JSON.parse(readFileSync(new URL('data/foundation-models-update.json',DIST),'utf8')).results['foundation-models-v9'];
  const peopleOf=track=>[...new Set(topics.rows.filter(r=>r.track===track).map(r=>r.participants))];
  const cardPins={
    'dry-vs-wet':{files:['deployment-topics.json'],pins:peopleOf('wearable-sensor-transfer')},
    'screen-to-vr':{files:['context-update.json','extension-update.json'],pins:[cx.results['vr-pc-p300'].cohort.people,ltr.cohort.people]},
    // Since 2026-10-04 the card also names BETA at eight and four electrodes for the v9 encoders, and its cohort.
    'fewer-electrodes':{files:['evidence-update.json','foundation-models-update.json'],pins:[ev.results.eesm23.cohort.people,ev.results.alphawaves.cohort.people,fmCard.protocols.find(p=>p.id==='beta-4ch').people],
      allow:[...ev.results.alphawaves.configurations.map(c=>c.channels.length),...fmCard.protocols.filter(p=>/^beta-/.test(p.id)).map(p=>p.channels)]},   // the zh card writes the electrode counts as digits
    'on-the-move':{files:['deployment-topics.json'],pins:[]},
    'calibration-budget':{files:['deployment-topics.json','large-source-update.json'],pins:[...peopleOf('wearable-calibration'),...new Set(topics.rows.filter(r=>r.track==='wearable-calibration').map(r=>r.labeled_target_trials).filter(n=>n>12)),
      lsx.results['openbmi-cross-session-calibration'].cohort.evaluated]},
    'model-adaptation':{files:['adaptation-update.json'],pins:[ad.results['eegmat-labram-adaptation'].cohort.people]},
    // Since 2026-10-04 the card names route 1's two primary cohorts as well.
    'when-not-to-act':{files:['experiments.json','extension-update.json','reliable-decisions-update.json'],pins:[...new Set(data.tracks.find(t=>t.id==='idle').rows.map(r=>r.subjects)),ysuX.cohort.people,
      ...['arithmetic-rest','beta-8ch'].map(p=>JSON.parse(readFileSync(new URL('../src/data/reliable-decisions-update.json',import.meta.url),'utf8')).results['reliable-decisions'].protocols[p].people)]},
    // Since 2026-10-04: the v9 checkpoints, counted, and (zh, in digits) how many lie above every published sleep row.
    'does-pretraining-help':{files:['deployment-topics.json','foundation-models-update.json'],pins:[fmCard.models.length],
      allow:[fmCard.comparisons.vs_published_rows.filter(x=>x.protocol==='sleep-scalp'&&['labram','cbramod','best_non_foundation'].every(k=>x[k].relation==='above')).length]},
    'clinical-groups':{files:['clinical-update.json'],pins:[cl.results.ds004584.cohort.people]},
    'sleep-staging':{files:['large-source-update.json'],pins:Object.values(lsx.results['dreem-sleep-baselines'].cohorts).map(c=>c.nights)},
    // Since 2026-10-07: OpenBMI's people only. No BOAS figure on a card: the home page and the hub do not carry
    // BOAS's three stated gaps (the route-2 pages block below holds that).
    'shared-encoder':{files:['shared-representation-update.json'],pins:[JSON.parse(readFileSync(new URL('data/shared-representation-update.json',DIST),'utf8')).results['one-representation'].datasets.openbmi.people]},
    // The later-sessions card counts people only where the export does: WBCIC-SHU's two cohorts and the RSVP cohort.
    // Forenzo counts records, not proven unique people, so its count stays off the card.
    'later-sessions':{files:['later-sessions-update.json'],pins:[...Object.values(LTX.results['wbcic-cross-session-cpu'].cohorts).map(c=>c.people),LTX.results['rsvp-later-visits'].cohort.people]},
  };
  assert.deepEqual(Object.keys(cardPins).sort(),topicPages.map(([s])=>s).sort(),'every topic card has its count pins');
  for(const page of ['','zh/']){
    const html=pageOf(page);
    for(const [slug,{files,pins,allow=[]}] of Object.entries(cardPins)){
      const at=html.search(new RegExp(`<a class="topic-entry-card" href="(?:/zh)?/topics/${slug}/"`));
      const card=visible(html.slice(at,html.indexOf('</a>',at)).replace(/<span class="topic-number"[^>]*>\d+<\/span>/,'')).replace(/[A-Za-z]+\d+/g,' ');
      const numbers=[...card.matchAll(/\d[\d,]*/g)].map(m=>Number(m[0].replace(/,/g,''))).filter(n=>n>1);
      for(const n of numbers) assert.ok(pins.includes(n)||allow.includes(n)||files.some(f=>leavesOf(f).has(n)),(page||'/')+' '+slug+' card: '+n+' is in none of its payloads');
      for(const n of pins) assert.ok(numbers.includes(n),(page||'/')+' '+slug+' card: must print '+n);
    }
  }
  // The transfer-coverage map, compact on the home page, full on the hub: cohort sizes and links only.
  const sortedPeople=track=>peopleOf(track).sort((a,b)=>b-a);
  const mapPins={'person:dry-vs-wet':peopleOf('wearable-sensor-transfer'),'person:model-adaptation':[ad.results['eegmat-labram-adaptation'].cohort.people],
    'person:mobile-ssvep':peopleOf('mobile-ssvep-2s'),'person:pretraining':sortedPeople('pretraining-attribution-fixed'),
    'session:mobile-erp':sortedPeople('mobile-erp'),'context:mobile-erp':sortedPeople('mobile-erp'),
    'session:cross-session':[cxs.feasibility.people],
    'sensor:dry-vs-wet':peopleOf('wearable-sensor-transfer'),
    'person:clinical':[cl.results.ds004584.cohort.people],'sensor:in-ear':[ev.results.eesm23.cohort.people],'sensor:posterior-subset':[ev.results.alphawaves.cohort.people],
    'context:screen-to-vr':[cx.results['vr-pc-p300'].cohort.people],'context:image-rate':[ltr.cohort.people],'context:mobile-ssvep':peopleOf('mobile-ssvep-2s'),
    // 2026-10-03: both Dreem cohorts behind one new-person entry, largest first; OpenBMI's evaluated people, next session.
    'person:sleep-staging':Object.values(lsx.results['dreem-sleep-baselines'].cohorts).map(c=>c.nights).sort((a,b)=>b-a),
    'session:openbmi':[lsx.results['openbmi-cross-session-calibration'].cohort.evaluated],
    // 2026-10-04: the v9 EEGMAT adaptation's people (new people, as the LaBraM adaptation), and BETA's people for
    // its eight-against-four-electrode comparison (two core protocols, a comparison, not a transfer).
    'person:v9-adaptation':[fmCard.eegmat_adaptation.people],'sensor:beta-montage':[fmCard.protocols.find(p=>p.id==='beta-4ch').people],
    // The later-sessions question: WBCIC-SHU's two cohorts, largest first, and the RSVP cohort. Forenzo prints no n
    // (records, not proven unique people), which the map loop below holds as a pin of nothing.
    'session:wbcic':Object.values(LTX.results['wbcic-cross-session-cpu'].cohorts).map(c=>c.people).sort((a,b)=>b-a),
    'session:rsvp':[LTX.results['rsvp-later-visits'].cohort.people]};
  for(const page of ['','zh/','topics/','zh/topics/']){
    const html=pageOf(page),table=html.slice(html.indexOf('<table class="tmap"'),html.indexOf('</table>',html.indexOf('<table class="tmap"')));
    assert.ok(table.length>500,(page||'/')+': the transfer-coverage map renders');
    assert.doesNotMatch(visible(table),/%|\bpp\b|个百分点|\d\.\d/,(page||'/')+': the map prints no score');
    const cells=[...table.matchAll(/<td\b[^>]*\bdata-state="([a-z]+)"[^>]*>([\s\S]*?)<\/td>/g)];
    assert.equal(cells.length,5*4,(page||'/')+': five rows of four states');
    for(const [, state, cell] of cells){
      if(state==='held') assert.ok(!cell.includes('data-fig')&&!/\d/.test(visible(cell)),(page||'/')+': a held map entry prints no figure');
      if(state==='held') for(const [,href] of cell.matchAll(/href="([^"]+)"/g)){
        assert.match(href,/^(?:\/zh)?\/releases\/#hold-[a-z0-9-]+$/,(page||'/')+': a held map entry links only its holds-register row');
        assert.ok(releasesHtml.includes(`<tr id="${href.split('#')[1]}"`),(page||'/')+': '+href+' names no register row');
      }
      if(state==='absent') assert.ok(!cell.includes('data-fig')&&!cell.includes('<a '),(page||'/')+': a not-measured entry has no link or cohort');
    }
    for(const [, key, body] of table.matchAll(/<li data-map="([^"]+)">([\s\S]*?)<\/li>/g)){
      const figs=[...body.matchAll(/<span data-fig="([^|"]+)\|count\|([^"]+)" class="num">([^<]+)<\/span>/g)];
      for(const [, file, raw, text] of figs){
        assert.ok(leavesOf(file).has(Number(raw)),(page||'/')+' '+key+': '+raw+' is not a value in '+file);
        assert.equal(text,fmt.count(Number(raw)),(page||'/')+' '+key+': printed as '+text);
      }
      if(figs.length) assert.ok(mapPins[key],(page||'/')+' '+key+': prints a cohort size that no pin holds');
      if(mapPins[key]) assert.deepEqual(figs.map(f=>Number(f[2])),mapPins[key],(page||'/')+' '+key+': the cohort sizes it must equal');
    }
    const keys=new Set([...table.matchAll(/<li data-map="([^"]+)">/g)].map(m=>m[1]));
    for(const key of Object.keys(mapPins)) assert.ok(keys.has(key),(page||'/')+': pinned map entry '+key+' must render');
    // An entry that changes two things at once says so in the compact map too.
    for(const key of ['session:mobile-erp','context:mobile-erp','context:image-rate','person:dry-vs-wet','sensor:dry-vs-wet','person:mobile-ssvep']){
      const li=table.slice(table.indexOf(`<li data-map="${key}">`),table.indexOf('</li>',table.indexOf(`<li data-map="${key}">`)));
      assert.match(li,/class="tmap-tag tmap-with">(?:also changes: |同时变化：)/,(page||'/')+' '+key+': names what else changes');
    }
  }
  // Holds on the home page are links: to their own page where the register gives one, else to their register row.
  for(const [page,prefix] of [['',''],['zh/','/zh']]){
    const html=pageOf(page),grid=html.slice(html.indexOf('<div class="hold-grid">'),html.indexOf('</div>',html.indexOf('<div class="hold-grid">')));
    const hrefs=[...grid.matchAll(/<a class="hold-card" href="([^"]+)"/g)].map(m=>m[1]);
    assert.ok(hrefs.length>=4&&!/<article class="hold-card"/.test(grid),(page||'/')+': every hold card is a link');
    for(const href of hrefs){
      const m=href.match(/^(?:\/zh)?\/releases\/#(hold-[a-z0-9-]+)$/);
      if(m) assert.ok(releasesHtml.includes(`<tr id="${m[1]}"`),(page||'/')+': '+href+' names no register row');
      else {
        const target=href.replace(/#.*$/,'').replace(/^\//,''),frag=href.includes('#')?href.split('#')[1]:null;
        assert.ok(existsSync(new URL(target+'index.html',DIST)),(page||'/')+': hold link '+href+' leads nowhere');
        if(frag) assert.ok(pageOf(target).includes(`id="${frag}"`),(page||'/')+': hold link '+href+' names no anchor on its page');
      }
    }
    const corr=releasesHtml.slice(releasesHtml.indexOf('id="corrections"'),releasesHtml.indexOf('</table>',releasesHtml.indexOf('id="corrections"')));
    const nCorrections=(corr.match(/<tr><th scope="row"><time /g)||[]).length;
    assert.ok(nCorrections>=2,'releases: the corrections register has its rows');
    assert.ok(html.includes(`<a href="${prefix}/releases/#corrections">`)&&visible(html).includes(page?`更正（${nCorrections}）`:`Corrections (${nCorrections})`),(page||'/')+': the corrections link counts the register ('+nCorrections+')');
  }
  // Directory band counts are the counts of what they link to; the old home anchors still land.
  const nReleases=(releasesHtml.match(/<article class="release-entry" id="/g)||[]).length;
  const nFiles=new Set([...pageOf('api/').matchAll(/href="\/data\/([^"]+)"/g)].map(m=>m[1])).size;
  for(const page of ['','zh/']){
    const html=pageOf(page);
    const counts=k=>[...html.matchAll(new RegExp(`<span data-count="${k}">(\\d+)</span>`,'g'))].map(m=>Number(m[1]));
    for(const k of ['questions','datasets','methods','releases','files']) assert.ok(counts(k).length&&new Set(counts(k)).size===1,(page||'/')+': '+k+' is counted, and the same wherever it is printed');
    const count=k=>counts(k)[0];
    assert.equal(count('releases'),nReleases,(page||'/')+': reviewed releases');
    assert.equal(count('files'),nFiles,(page||'/')+': downloadable files, as listed on /api/');
    assert.equal(count('methods'),entityPages.filter(f=>!f.startsWith('zh/')&&/^methods\/[^/]+\/index\.html$/.test(f)).length,(page||'/')+': methods with result pages');
    assert.equal(count('datasets'),entityPages.filter(f=>!f.startsWith('zh/')&&/^datasets\/[^/]+\/index\.html$/.test(f)).length,(page||'/')+': datasets with results');
    assert.equal(count('questions'),topicPages.length,(page||'/')+': questions');
    for(const id of ['models','datasets','news']) assert.ok(html.includes(`id="${id}"`),(page||'/')+': the old #'+id+' anchor still lands');
    assert.ok(!html.includes('class="model-grid"')&&!html.includes('class="dataset-list"')&&!html.includes('class="news-grid"'),(page||'/')+': the directory, register and field notes left the home page');
  }
  // The moved sections: every model card, every register row, every field note, with the status-checked date.
  // Since 2026-10-04 the directory also carries the v9 entries the export suggests (REVE Base keeps its
  // released card; EEGPT is unchanged; "MIRepNet, EEG-DINO" are two catalogue-only cards).
  const fmDir=JSON.parse(readFileSync(new URL('../src/data/foundation-models-update.json',import.meta.url),'utf8')).results['foundation-models-v9'].directory_status;
  const fmCards=fmDir.filter(x=>!['REVE Base','EEGPT'].includes(x.name)).flatMap(x=>/, /.test(x.name)&&!/\(/.test(x.name)?x.name.split(', '):[x.name]);
  for(const page of ['methods/','zh/methods/']){
    const html=pageOf(page);
    for(const m of data.models) assert.ok(html.includes(`<article class="model-card" data-model="${m.name.replace(/&/g,'&amp;')}">`),page+': model card for '+m.name);
    assert.equal((html.match(/<p class="status-checked">/g)||[]).length,data.models.length+fmCards.length,page+': every model card says when its status was checked');
    for(const n of data.news) assert.ok(html.includes(n.sourceUrl.replace(/&/g,'&amp;')),page+': field note '+n.title.slice(0,30));
    // Follow-up review of 2026-10-05: the REVE note of 2025-10-24 keeps its words ("not yet available in our local test
    // pool"), and a note after it says REVE Base and Large have since been evaluated, linking REVE's method page. Since
    // 2026-10-08 (owner decision) the note's words carry no date; data-later still names the release date for this check.
    {const zh=page.startsWith('zh/'),n=data.news.find(x=>/not yet available in our local test pool/.test(x.summary));
     const a0=html.lastIndexOf('<article',html.indexOf(escHtml(n.title)+' ↗</a></h3>')),card=html.slice(a0,html.indexOf('</article>',a0));
     const fmDate=JSON.parse(readFileSync(new URL('data/foundation-models-update.json',DIST),'utf8')).generated_at;
     assert.ok(card.includes('<p>'+escHtml(n.summary)+'</p>'),page+': the REVE field note keeps its released words');
     const later=card.match(/<p class="news-later" data-later="([^"]+)"[^>]*>([\s\S]*?)<\/p>/);
     assert.ok(later&&later[1]===fmDate&&!later[2].includes(fmDate)&&!/\bv9\b|第九轮/.test(later[2])&&/REVE Base/.test(later[2])&&/REVE Large/.test(later[2])&&later[2].includes(`href="${zh?'/zh':''}/methods/reve/"`)&&card.indexOf('news-later')>card.indexOf(escHtml(n.summary)),
       page+': the REVE field note carries a note, after its words and with no date in them, that REVE Base and Large have since been evaluated');}
    // REVE Base: evaluated since 2026-10-04 (the owner accepted the REVE Responsible Use License), with its
    // source and checked date, the released status beside it; the 2026-10-02 "Licence review pending" is gone.
    const reve=html.slice(html.indexOf('data-model="REVE Base"'),html.indexOf('</article>',html.indexOf('data-model="REVE Base"')));
    assert.ok(reve.includes('class="status-override"')&&reve.includes('https://huggingface.co/brain-bzh/reve-base')&&reve.includes('2026-10-04'),page+': REVE Base override, source and date');
    assert.match(reve,page.startsWith('zh')?/<span class="status ready">已评测<\/span>/:/<span class="status ready">Evaluated<\/span>/,page+': REVE Base shows the checked status');
    assert.match(reve,page.startsWith('zh')?/访问受限/:/Access gated/,page+': REVE Base keeps the released status beside it');
    assert.doesNotMatch(reve,/许可审查中|Licence review pending/,page+': the 2026-10-02 licence-review status is replaced');
    assert.match(reve,page.startsWith('zh')?/REVE Responsible Use License v1\.0/:/accepted the REVE Responsible Use License v1\.0/,page+': REVE Base names the accepted licence');
    assert.ok(reve.includes(`href="/${page.startsWith('zh')?'zh/':''}methods/reve/"`),page+': REVE Base leads to its method page');
  }
  for(const page of ['datasets/','zh/datasets/']){
    const html=pageOf(page);
    for(const d of data.datasets) assert.ok(html.includes(`<article class="dataset-row" data-dataset="${d.name.replace(/&/g,'&amp;')}">`),page+': register row for '+d.name);
  }
  // 404 points at the hubs.
  const nf=readFileSync(new URL('404.html',DIST),'utf8');
  for(const href of ['/topics/','/methods/','/datasets/','/releases/#holds']) assert.ok(nf.includes(`href="${href}"`),'404: links '+href);
}
console.log('PASS: 2026-10-02 home and hubs — one navigation everywhere with the current page marked; Questions hub and breadcrumbs; every topic card once, grouped, with its counts from its payloads; transfer map with cohort sizes only, pinned, held entries figure-free; hold cards link; corrections counted; directory band counts; directory, register and field notes moved with their status dates and the REVE override; 404 hubs.');

// --- 2026-10-04 route 1, reliable decisions ------------------------------------------------
// The first route of the decision-research roadmap, run (owner approval 2026-10-04): its own
// section, #reliable-decisions, after the idle methods and limits and before the roadmap, whose
// slice stays figure-free. Every figure there is printed with data-fig and re-read from
// reliable-decisions-update.json (the topic data-fig loop below); pinned here is what must travel
// with those figures and what must never be said: method comparisons, never deployment rates;
// nothing accepted is "not defined", never 0%; fewer than ten accepted is a count with a flag;
// every contrast carries the verdict its interval supports; no ranking; people with nothing
// accepted beside every coverage; the secondary arms collapsed, ds003810 crude; idle and
// BNCI2015-001 without a figure.
{
  const releasesHtml=pageOf('releases/');
  const rdx=JSON.parse(readFileSync(new URL('../src/data/reliable-decisions-update.json',import.meta.url),'utf8'));
  assert.deepEqual(readFileSync(new URL('../src/data/reliable-decisions-update.json',import.meta.url)),readFileSync(new URL('../public/data/reliable-decisions-update.json',import.meta.url)),
    'source and downloadable reliable-decisions exports must be byte-identical');
  assert.deepEqual(Object.keys(rdx.results),['reliable-decisions'],'one result, route 1');
  assert.deepEqual([rdx.status_only,rdx.holds],[[],[]],'route 1 has no status-only source and no hold');
  const R=rdx.results['reliable-decisions'],E=R.protocols['arithmetic-rest'],B=R.protocols['beta-8ch'],M=R.robustness.mi_rest;
  const mid=(p,id)=>p.methods.find(m=>m.id===id);
  // What the file says it carries (review of 2026-10-05). The candidate's first boundary said class-conditional rows
  // are given so readers can re-weight to another prevalence; the export refuses those rows, so the boundary says they
  // were not carried and not_published names them as they are (pooled per class, not person-level spreads). The
  // BNCI2015-001 hold carries the date its register row gives it.
  assert.ok(R.boundaries.all_protocols.every(b=>!/rows are given/.test(b))&&/class-conditional rows \(acceptance per class\)[^.]* are not carried into this file\.$/.test(R.boundaries.all_protocols[0]),
    'route 1: the boundary must not promise class-conditional rows the file does not carry');
  assert.ok(rdx.not_published.some(x=>/class-conditional rows/.test(x)&&/acceptance per class/.test(x))&&!rdx.not_published.some(x=>/per-class acceptance spreads/.test(x)),
    'route 1: not_published names the class-conditional rows as they are');
  {
    const reg=releasesHtml.slice(releasesHtml.indexOf('<tr id="hold-bnci2015-001-crossday"'),releasesHtml.indexOf('</tr>',releasesHtml.indexOf('<tr id="hold-bnci2015-001-crossday"')));
    const opened=reg.match(/<time datetime="(\d{4}-\d\d-\d\d)">/)[1],item=rdx.not_published.filter(x=>x.includes('BNCI2015-001'));
    assert.ok(item.length===1&&item[0].includes('opened on '+opened),'route 1: the BNCI2015-001 hold is dated as its register row dates it ('+opened+')');
  }
  // The handoff's headline figures, so a changed export cannot pass by changing the page with it.
  assert.deepEqual(B.methods.map(m=>[m.id,pct1(m.fixed_cutoff.coverage),m.fixed_cutoff.people_with_nothing_accepted]),[['cca','28.4%',0],['cbramod','1.5%',38],['eegnet','16.6%',10]],'BETA fixed-threshold coverage and people with nothing accepted');
  assert.deepEqual(E.methods.map(m=>[m.id,m.fixed_cutoff.accepted,m.fixed_cutoff.people_with_nothing_accepted]),[['spectral-ridge',3,33],['eegnet',126,19],['labram-frozen-ce',1,35],['labram-lora-r4',44,24]],'EEGMAT fixed-threshold accepted and people with nothing accepted');
  assert.deepEqual([...E.methods,...B.methods].map(m=>pct1(m.balanced_accuracy)),['56.8%','67.6%','56.9%','64.4%','63.1%','33.7%','55.8%'],'full-coverage accuracies, the published ones');
  assert.deepEqual([E,B].flatMap(p=>p.methods.filter(m=>m.learned_minus_confidence.error_at_80.excludes_zero).map(m=>p.protocol+'/'+m.id)),['arithmetic-rest/eegnet','arithmetic-rest/labram-lora-r4','beta-8ch/eegnet'],'C2 resolved where the handoff says');
  assert.ok([E,B].every(p=>p.methods.every(m=>!(m.learned_minus_confidence.error_at_80.excludes_zero&&m.learned_minus_confidence.error_at_80.mean<0))),'L had a lower error than S for no method');
  assert.deepEqual(B.methods.map(m=>[m.risk_certification.certified_folds,m.risk_certification.folds_over_target]),[[7,4],[4,2],[7,2]],'BETA certified folds and folds over target');
  assert.ok(E.methods.every(m=>m.risk_certification.certified_folds===0&&m.risk_certification.accepted===0&&m.risk_certification.selective_error===null),'EEGMAT: nothing certified, nothing accepted, no error rate');
  assert.equal(B.common_coverage.accepted,165,'matched coverage on BETA: 165 trials');
  assert.ok(E.common_coverage.unstable&&!E.common_coverage.errors,'matched coverage on EEGMAT: unstable, no verdict');
  // Formatting and tokens, as the site prints them.
  const sgn3=v=>(v>=0?'+':'−')+Math.abs(v).toFixed(3);
  const tokensOfRd=obj=>{const out=new Set();const walk=v=>{if(typeof v==='number'){for(const g of fmtEarlier)for(const n of numbers(g(v)))out.add(n);}
    else if(typeof v==='string'){for(const n of numbers(v))out.add(n);}else if(v&&typeof v==='object')Object.values(v).forEach(walk);};walk(obj);return out;};
  const rdTokens=tokensOfRd(rdx);
  const figureLikeRd=t=>[...t.matchAll(/\d+\.\d+|\d{1,3}(?:,\d{3})+/g)].map(m=>m[0]);
  const verdictWord={en:['difference resolved','no difference resolved'],zh:['可以认定有差异','不能认定有差异']};
  const rdSec=html=>{const a=html.indexOf('<section class="topic-section" id="reliable-decisions"');assert.ok(a>0,'the reliable-decisions section must render');return html.slice(a,html.indexOf('</section>',a));};
  const cellAt=(sec,attr)=>{const a=sec.indexOf(attr);assert.ok(a>0,'missing '+attr);const s0=sec.lastIndexOf('<td',a),open=s0>sec.lastIndexOf('</td>',a)?s0:a;return sec.slice(open,sec.indexOf('</td>',a));};
  const rowAt=(sec,attr)=>{const a=sec.indexOf(attr);assert.ok(a>0,'missing row '+attr);return sec.slice(a,sec.indexOf('</tr>',a));};
  const hasRd=(h,f,x)=>h.includes(`data-fig="reliable-decisions-update.json|${f}|${x}"`);
  // The formats the site picks (review of 2026-10-05): a second decimal where one would print ±0.0 or 0.0%.
  const ppF=v=>Math.abs(v*100)<0.05?'pp2':'pp1',sgF=v=>Math.abs(v*100)<0.05?'sgn2':'sgn1',covF=v=>v>0&&v<0.0005?'pct2':'pct1';
  const figsetRd=h=>[...h.matchAll(/data-fig="([^"]+)"/g)].map(m=>m[1]).sort();
  for(const [label,path] of [['en','topics/when-not-to-act/'],['zh','zh/topics/when-not-to-act/']]){
    const zh=label==='zh',html=pageOf(path),sec=rdSec(html),text=visible(sec),where=label+'/when-not-to-act #reliable-decisions';
    const [yes,no]=verdictWord[label];
    // A verdict cell: every data-resolved in it equals the export's, and its words are exactly the matching ones
    // ("no difference resolved" contains "difference resolved", so a substring test would pass a flipped verdict).
    const verdictIs=(cell,resolved)=>{const attrs=[...cell.matchAll(/data-resolved="(true|false)"/g)].map(m=>m[1]);
      const words=[...cell.matchAll(/<span class="verdict"[^>]*>([^<]*)<\/span>/g)].map(m=>m[1]);
      return attrs.length>=2&&attrs.every(a=>a===String(resolved))&&words.length===1&&words[0]===(resolved?yes:no);};
    // Placement: after the idle methods and limits, before the roadmap.
    const at=html.indexOf('id="reliable-decisions"');
    assert.ok(at>html.indexOf('id="methods-and-limits"')&&at<html.indexOf('id="decision-research"')&&at>html.indexOf('id="non-control"'),where+': between methods and limits and the roadmap');
    // Every figure from the export: data-fig only from this file; every figure-like token is one of its values.
    assert.ok([...sec.matchAll(/data-fig="([^|"]+)\|/g)].every(m=>m[1]==='reliable-decisions-update.json'),where+': every figure is a leaf of the route-1 export');
    for(const t of figureLikeRd(text)) assert.ok(rdTokens.has(t),where+': "'+t+'" is not a value of the route-1 export');
    // Q1: every protocol panel, every method in the export's order, people with nothing accepted beside the coverage bar.
    for(const p of [B,E]){
      const rows=[...sec.matchAll(new RegExp(`data-rd-row="${p.protocol}\\|([^"]+)"`,'g'))].map(m=>m[1]);
      assert.deepEqual(rows,p.methods.map(m=>m.id),where+': '+p.protocol+' methods in the export\'s order, not ranked');
      for(const m of p.methods){
        const F=m.fixed_cutoff,row=rowAt(sec,`data-rd-row="${p.protocol}|${m.id}"`);
        for(const [f,x] of [['pct1',m.balanced_accuracy],['count',F.accepted],['count',F.n],[covF(F.coverage),F.coverage],['count',F.people_with_nothing_accepted],['count',p.people],['pct1',m.coverage_target.coverage]])
          assert.ok(hasRd(row,f,x),where+': '+p.protocol+'/'+m.id+' row prints '+f+' '+x);
        assert.ok(row.includes('score-bar-svg')&&row.indexOf('score-bar-svg')<row.indexOf('data-cell="nothing-accepted"'),where+': '+m.id+' people with nothing accepted sit beside the coverage bar');
        const err=cellAt(row,'data-cell="fixed-error"');
        if(F.selective_error===null){
          assert.ok(err.includes('data-null="true"')&&!/\d/.test(visible(err)),where+': '+m.id+' nothing accepted: a dash and its reason, no number');
        } else if(F.accepted<R.design.unstable_below_accepted){
          assert.ok(err.includes('data-unstable="true"')&&hasRd(err,'count',F.accepted_wrong)&&!/%/.test(visible(err)),where+': '+m.id+' fewer than ten accepted: a count with a flag, never a rate');
          assert.match(visible(err),zh?/不稳定：被接受的少于 10 个/:/Unstable: fewer than 10 accepted/,where+': '+m.id+' the unstable flag');
        } else assert.ok(hasRd(err,'pct1',F.selective_error)&&hasRd(err,'pct1',F.selective_error_interval_95[0]),where+': '+m.id+' error among accepted with its interval');
      }
      for(const d of p.fixed_cutoff_coverage_differences){
        const row=rowAt(sec,`data-rd-pair="${p.protocol}|${d.a}|${d.b}"`);
        assert.ok(hasRd(row,ppF(d.mean),d.mean)&&hasRd(row,sgF(d.interval_95[0]),d.interval_95[0])&&hasRd(row,ppF(d.interval_95[1]),d.interval_95[1]),where+': coverage difference '+d.a+' − '+d.b);
        assert.ok(verdictIs(row,d.excludes_zero),where+': coverage difference '+d.a+' − '+d.b+' carries its verdict');
      }
    }
    // Matched coverage: BETA errors and differences with verdicts; EEGMAT unstable, without an error figure.
    for(const e of B.common_coverage.errors) assert.ok(hasRd(rowAt(sec,`data-rd-matched="${e.id}"`),'pct1',e.mean),where+': matched-coverage error '+e.id);
    for(const d of B.common_coverage.differences){const row=rowAt(sec,`data-rd-pair="matched|${d.a}|${d.b}"`);
      assert.ok(verdictIs(row,d.excludes_zero),where+': matched difference '+d.a+' − '+d.b+' verdict');}
    const un=sec.slice(sec.indexOf('data-rd-unstable="arithmetic-rest"'),sec.indexOf('</p>',sec.indexOf('data-rd-unstable="arithmetic-rest"')));
    assert.ok(hasRd(un,'count',E.common_coverage.accepted)&&!/%/.test(visible(un))&&(zh?/不作判定/:/no verdict/).test(visible(un)),where+': EEGMAT matched coverage is unstable, no verdict, no rate');
    // Q2: both measures, levels with intervals, both contrasts with their verdicts.
    for(const p of [E,B]) for(const m of p.methods){
      const row=rowAt(sec,`data-rd-learned="${p.protocol}|${m.id}"`),d1=m.learned_minus_confidence.aurc,d2=m.learned_minus_confidence.error_at_80;
      for(const [f,x] of [['num3',m.ranking_S.aurc.mean],['num3',m.ranking_L.aurc.mean],['sgn3',d1.mean],['pct1',m.ranking_S.error_at_80.mean],['pct1',m.ranking_L.error_at_80.mean],[ppF(d2.mean),d2.mean],[sgF(d2.interval_95[0]),d2.interval_95[0]],['sgn3',d1.interval_95[1]]])
        assert.ok(hasRd(row,f,x),where+': '+p.protocol+'/'+m.id+' Q2 prints '+f+' '+x);
      for(const [k,d] of [['c1',d1],['c2',d2]]) assert.ok(verdictIs(cellAt(row,`data-diff="${k}"`),d.excludes_zero),where+': '+m.id+' '+k+' verdict');
    }
    assert.match(text,zh?/在 80% 覆盖率下，没有一种方法上 L 的错误率比 S 低；凡是能认定有差异的，都是 L 错得更多。/:/L had a lower error than S at 80% for no method; where a difference was resolved, L erred more\./,where+': the Q2 reading');
    // Q3: certified folds, folds over target, nothing accepted is not defined.
    for(const p of [B,E]) for(const m of p.methods){
      const R3=m.risk_certification,row=rowAt(sec,`data-rd-risk="${p.protocol}|${m.id}"`);
      assert.ok(hasRd(row,'count',R3.certified_folds)&&hasRd(row,'count',R3.outer_folds),where+': '+m.id+' certified folds');
      const er=cellAt(row,'data-cell="risk-error"');
      if(R3.accepted===0){
        assert.ok(er.includes('data-null="true"')&&!/\d/.test(visible(er))&&visible(er).includes(zh?'没有定义':'not defined'),where+': '+p.protocol+'/'+m.id+' nothing accepted: no error rate, not a zero one');
        assert.ok(!/\d/.test(visible(cellAt(row,'data-cell="c6"'))),where+': '+m.id+' no error-minus-target without anything accepted');
      } else {
        assert.ok(hasRd(er,'pct1',R3.selective_error)&&hasRd(row,'pct1',R3.target_weighted)&&hasRd(cellAt(row,'data-cell="over"'),'count',R3.folds_over_target),where+': '+m.id+' error, target and folds over target');
        const c6=cellAt(row,'data-cell="c6"');
        assert.ok(hasRd(c6,ppF(R3.error_minus_target.mean),R3.error_minus_target.mean)&&verdictIs(c6,R3.error_minus_target.excludes_zero),where+': '+m.id+' error minus target with its verdict');
      }
    }
    assert.match(text,zh?/名义保证/:/nominal guarantee/,where+': S-risk is a nominal guarantee');
    assert.doesNotMatch(text,zh?/保证不超过|确保错误率/:/\bguarantees? (?:that )?the error|is guaranteed\b/i,where+': no certified risk is read as a guarantee');
    // Q5: labels per new person beside every recalibration row; each change with its verdict.
    for(const p of [B,E]) for(const m of p.methods) for(const x of m.recalibration){
      const row=rowAt(sec,`data-rd-recal="${p.protocol}|${m.id}|${x.prefix}"`);
      assert.ok(hasRd(cellAt(row,'data-cell="labels"'),'count',x.labels_per_new_person),where+': '+m.id+' '+x.prefix+' labels per new person');
      for(const [k,d] of [['nll',x.nll_change],['ece',x.ece_change],['aurc',x.aurc_change],['gap',x.unlabelled_cutoff_gap_change]])
        assert.ok(verdictIs(cellAt(row,`data-diff="${k}"`),d.excludes_zero)&&hasRd(row,k==='gap'?ppF(d.mean):'sgn3',d.mean),where+': '+m.id+' '+x.prefix+' '+k+' with its verdict');
    }
    assert.ok(sec.includes(zh?'每名新被试的标签数':'Labels per new person'),where+': the label cost is a column');
    // Q4: one sentence, its contrast and its link.
    const lora=E.lora_minus_head_only,q4=sec.slice(sec.indexOf('id="rd-lora"'),sec.indexOf('id="rd-quality"'));
    assert.ok(hasRd(q4,'sgn3',lora.nll_calibrated.mean)&&hasRd(q4,'sgn3',lora.ece_calibrated.mean)&&q4.includes(`href="${zh?'/zh':''}/topics/model-adaptation/"`),where+': the LoRA sentence, its figures and link');
    assert.match(visible(q4),zh?/ECE 不能认定有差异/:/For ECE, no difference resolved/,where+': ECE not resolved, said so');
    // Probability quality: raw is "not applicable", never a number, where the score has no probability.
    for(const p of [E,B]) for(const m of p.methods){
      const row=rowAt(sec,`data-rd-quality="${p.protocol}|${m.id}"`),q=m.probability_quality;
      assert.ok(hasRd(row,'num3',q.calibrated.nll.mean)&&hasRd(row,'num3',q.calibrated.ece.mean)&&hasRd(row,'num3',q.calibrated.brier.mean),where+': '+m.id+' calibrated quality');
      if(q.raw===null) assert.equal((row.match(/data-na="true"/g)||[]).length,2,where+': '+m.id+' raw quality not applicable, twice, no number');
      else assert.ok(hasRd(row,'num3',q.raw.nll.mean)&&!row.includes('data-na'),where+': '+m.id+' raw quality');
    }
    // The robustness panel: collapsed by default; ds003810 labelled crude; the sensitivity arms print fold counts only.
    const panelAt=sec.indexOf('<details class="rd-panel" id="rd-robustness">');
    assert.ok(panelAt>0,where+': the robustness panel is collapsed by default');
    const panel=sec.slice(panelAt,sec.indexOf('</details>',panelAt));
    assert.match(visible(panel),zh?/ds003810，运动想象与静息：粗略/:/ds003810, motor imagery and rest: crude/,where+': ds003810 labelled crude');
    for(const m of M.methods) assert.ok(panel.includes(`data-rd-crude="${m.id}"`)&&!sec.slice(0,panelAt).includes(`|${m.balanced_accuracy}"`),where+': ds003810 '+m.id+' only in the panel');
    assert.equal((panel.match(/data-rd-seed=/g)||[]).length,R.robustness.seeds.rows.length,where+': every secondary seed row');
    const sens=panel.slice(panel.indexOf('data-rd-sensitivity="true"'),panel.indexOf('</table>',panel.indexOf('data-rd-sensitivity="true"')));
    assert.ok(sens.length>200&&!/%|\d\.\d/.test(visible(sens)),where+': sensitivity arms print fold counts only, never an accuracy');
    assert.equal((panel.match(/data-rd-ljoint=/g)||[]).length,2,where+': the jointly trained reject head on both protocols');
    const left=panel.slice(panel.indexOf('id="rd-left-out"'),panel.indexOf('</p>',panel.indexOf('id="rd-left-out"')));
    assert.ok(left.length>100&&!/\d+(?:\.\d+)?\s?%|\d\.\d|\bpp\b/.test(visible(left))&&!left.includes('data-fig'),where+': idle and BNCI2015-001 left out, figure-free');
    assert.ok(left.includes(`href="${zh?'/zh':''}/releases/#hold-bnci2015-001-crossday"`)&&releasesHtml.includes('<tr id="hold-bnci2015-001-crossday"'),where+': the BNCI2015-001 hold links its register row');
    // The required limitations, in the page's language.
    for(const re of zh?[/没有一个是部署时的错误率/,/每个类别各自是一段记录/,/没有空闲状态，所以给不出任何形式的误触发数字/,/覆盖率为零时没有错误率，而不是错误率为零/,/被接受的少于 10 个时标为不稳定/,/这个保证只是名义上的：它失效的频率在这里是测出来的，不是假设的/,
                        /拒绝已知类别上可能判错的试次，不等于识别陌生的输入/,/第一条路线不作任何分布外的声明/,/约四分之三训练被试/,/全覆盖时的准确率都等于本站已发布的数值/,/它们的准确率不发布，也绝不与本站的数值混在一起/,
                        /不做多重比较校正/,/区间重叠时不排名/,/从来不是每小时的误触发率/,/与本页的空闲数字单位不同/,/bootstrap 区间粗略/]
                     :[/none is a deployment error rate/,/each class is its own recording/,/no idle state, so it gives no false-activation figure of any kind/,/At zero coverage there is no error rate, not a zero one/,/fewer than 10 accepted trials are flagged unstable/,/the guarantee is nominal: how often it fails is measured here, not assumed/,
                        /Rejecting likely errors on known classes is not detecting unfamiliar input/,/Route 1 makes no out-of-distribution claim/,/about three quarters of the training people/,/every full-coverage accuracy equals the site’s published value/,/their accuracies are not published and are never mixed with the site’s/,
                        /no multiplicity correction/,/Nothing is ranked where intervals overlap/,/never a false-activation rate per hour/,/in a different unit from this page’s idle figures/,/bootstrap intervals are crude/])
      assert.match(text,re,where+': required limitation '+re);
    // Never a deployment rate, a ranking or an out-of-distribution claim.
    if(!zh) for(const m of text.matchAll(/deployment (?:error )?rates?/g)) assert.match(text.slice(Math.max(0,m.index-45),m.index),/\bnot\b|\bno\b|\bnone\b|\bnever\b/,where+': "'+m[0]+'" reads as a claim');
    else for(const m of text.matchAll(/部署时的(?:错误率|比率)|部署比率/g)) assert.match(text.slice(Math.max(0,m.index-14),m.index),/不是|没有|从来不是|没有一个是/,where+': "'+m[0]+'" reads as a claim');
    assert.doesNotMatch(text,zh?/排名第一|最好的方法|胜出|优于其他/:/\b(?:best|worst|outperform\w*|winner|ranks? first|top-ranked)\b/i,where+': nothing is ranked');
    assert.doesNotMatch(text,zh?/(?<!不等于)识别陌生的输入|能检测分布外/:/(?<!not )detect(?:s|ing)? (?:unfamiliar|out-of-distribution)/i,where+': no out-of-distribution claim');
    // Credits: the three recordings and the six method sources, the export linked, the audit counts printed.
    for(const s0 of ['10.13026/C2JQ1P','10.3389/fnins.2020.00627','https://doi.org/10.18112/openneuro.ds003810.v2.0.2',...R.literature.map(l=>l.url)]) assert.ok(sec.includes(s0),where+': credit '+s0);
    assert.ok(sec.includes('href="/data/reliable-decisions-update.json"'),where+': the reviewed export is linked');
    const aud=sec.slice(sec.indexOf('id="rd-audits"'),sec.indexOf('</p>',sec.indexOf('id="rd-audits"')));
    for(const x of [R.audits.independent_primary.passed,R.audits.independent_primary.checks,R.audits.independent_secondary.checks]) assert.ok(hasRd(aud,'count',x),where+': audit count '+x);
    assert.match(visible(aud),zh?/文档错误，不是计算错误/:/a documentation error, not a computation error/,where+': the failed audit check is documentation, said so');
    // Review of 2026-10-05. A value that would print ±0.0 or 0.0% gets a second decimal, so a bound of +0.02 (resolved)
    // and one of exactly 0 (not) no longer print alike, and one window in 2,160 is not a coverage of 0.0%.
    const zeroLike=h=>[...h.matchAll(/data-fig="reliable-decisions-update\.json\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)].filter(([,f,raw,t])=>Number(raw)!==0&&/^[+−]?0\.0(?: pp|%)?$/.test(t));
    assert.deepEqual(zeroLike(sec).map(m=>m[0]),[],where+': no non-zero figure prints as ±0.0 or 0.0%');
    // The two LaBraM arms are the 1 October release's seed-20260922 means, and say so (the three-seed means differ).
    for(const id of ['labram-frozen-ce','labram-lora-r4']) assert.ok(visible(cellAt(rowAt(sec,`data-rd-row="arithmetic-rest|${id}"`),'data-cell="ba"')).includes(zh?'已发布的随机种子 20260922 均值（适配发布）':'the published seed-20260922 mean, adaptation release'),where+': '+id+' is labelled as the seed-20260922 mean');
    for(const p of [E,B]) for(const m of p.methods.filter(m=>!m.id.startsWith('labram-'))) assert.ok(!/20260922/.test(cellAt(rowAt(sec,`data-rd-row="${p.protocol}|${m.id}"`),'data-cell="ba"')),where+': '+m.id+' is not a LaBraM seed mean');
    assert.ok(text.includes(zh?'两种 LaBraM 配置用的是适配发布中随机种子 20260922 的均值':'for the two LaBraM arms, the adaptation release’s seed-20260922 mean'),where+': the lede says which LaBraM value is printed');
    assert.ok(visible(q4).includes(zh?'随机种子 20260922':'seed 20260922'),where+': the LoRA sentence says its accuracies are seed 20260922');
    // ds003810's contrasts are secondary, and say so; the two protocols' rejection gains are not compared.
    const crude=sec.slice(sec.indexOf('id="rd-crude"'),sec.indexOf('</table>',sec.indexOf('id="rd-crude"')));
    assert.ok(!/no primary contrast|也没有主要对比/.test(visible(crude))&&visible(crude).includes(zh?'下面的对比是次要对比':'Its contrasts below are secondary'),where+': ds003810\'s contrasts are called secondary');
    assert.ok(!/falls only from|只从/.test(text)&&text.includes(zh?'两个协议之间不作比较':'the two are not compared'),where+': BETA and EEGMAT rejection gains are not compared');
    // Follow-up review of 2026-10-05: "differs by protocol" was itself a comparison across protocols; the gain is read
    // per protocol. And the EEGMAT NLL rise is counted where its interval excludes zero (EEGNet's point estimate rose
    // too, unresolved), so the sentence says so.
    assert.ok(text.includes(zh?'拒识能换来多少，按协议分别来读':'How much declining buys is read per protocol')&&!/declining buys differs by protocol|拒识能换来多少，因协议而异/.test(text),where+': the rejection gain is read per protocol, not said to differ');
    {const k5=E.methods.map(m=>m.recalibration.find(x=>x.prefix==='k5')),up=k5.filter(x=>x.nll_change.excludes_zero&&x.nll_change.mean>0).length;
     assert.ok(up===3&&k5.some(x=>!x.nll_change.excludes_zero&&x.nll_change.mean>0),'route 1: three resolved NLL rises at 10 labels, and one unresolved point-estimate rise');
     assert.ok(text.includes(zh?'四种方法中有三种的 NLL 上升，且区间不含零':'NLL rose, with the interval excluding zero, for three of the four methods'),where+': the NLL rise is counted where its interval excludes zero');}
    // The idle limit on the same page no longer says probability quality is unmeasured everywhere.
    assert.ok(html.includes(zh?'这个协议上没有测概率质量':'No probability quality on this protocol'),where+': the idle limit is scoped to its protocol');
  }
  assert.deepEqual(figsetRd(rdSec(pageOf('zh/topics/when-not-to-act/'))),figsetRd(rdSec(pageOf('topics/when-not-to-act/'))),'#reliable-decisions: the same figures in both languages');
  // The model-adaptation page links the probability quality of its own arms (route 1's Q4), figure-free.
  for(const pfx of ['','zh/']){
    const html=pageOf(pfx+'topics/model-adaptation/'),a=html.indexOf('<p class="protocol-note" id="rd-pointer">'),ptr=html.slice(a,html.indexOf('</p>',a));
    assert.ok(a>html.indexOf('id="adaptation"')&&a<html.indexOf('id="next-day"')&&ptr.includes(`href="/${pfx}topics/when-not-to-act/#rd-lora"`)&&pageOf(pfx+'topics/when-not-to-act/').includes('id="rd-lora"'),pfx+'topics/model-adaptation/: the route-1 pointer lands on the LoRA sentence');
    assert.doesNotMatch(visible(ptr),/\d+\.\d|%|\bpp\b/,pfx+'topics/model-adaptation/: the route-1 pointer carries no figure');
  }
  // Dataset and method pages: one route-1 group per dataset, each C2 row with its verdict and each coverage with the people who had nothing accepted.
  for(const [label,pfx] of [['en',''],['zh','zh/']]){
    for(const [ds,p] of [['eegmat',E],['beta',B],['ds003810',M]]){
      const h=pageOf(pfx+'datasets/'+ds+'/'),g0=h.indexOf('id="g-reliable-decisions"'),g=h.slice(g0,h.indexOf('</section>',g0));
      assert.ok(g0>0,label+'/datasets/'+ds+': the route-1 group');
      assert.ok(g.includes(`href="${pfx?'/zh':''}/topics/when-not-to-act/"`),label+'/datasets/'+ds+': the group links its topic');
      if(ds==='ds003810') assert.match(g,label==='zh'?/粗略/:/crude/,label+'/datasets/ds003810: labelled crude');
      const zl=[...g.matchAll(/data-fig="reliable-decisions-update\.json\|(\w+)\|([^"]+)"[^>]*>([^<]*)</g)].filter(([,f,raw,t])=>Number(raw)!==0&&/^[+−]?0\.0(?: pp|%)?$/.test(t));
      assert.deepEqual(zl.map(m=>m[0]),[],label+'/datasets/'+ds+': no non-zero route-1 figure prints as ±0.0');
      for(const m of p.methods){
        assert.ok(hasRd(g,'count',m.fixed_cutoff.accepted)&&hasRd(g,'count',m.fixed_cutoff.people_with_nothing_accepted),label+'/datasets/'+ds+': '+m.id+' accepted with people who had nothing accepted');
        const d=m.learned_minus_confidence.error_at_80,at=g.indexOf(`data-fig="reliable-decisions-update.json|${ppF(d.mean)}|${d.mean}"`),row=g.slice(at,g.indexOf('</tr>',at));
        assert.ok(at>0&&(label==='zh'?(d.excludes_zero?/可以认定有差异/:/不能认定有差异/):(d.excludes_zero?/Difference resolved/:/No difference resolved/)).test(row),label+'/datasets/'+ds+': '+m.id+' C2 verdict beside the figure');
      }
    }
    for(const mp of ['eegnet','labram','cbramod','cca']) assert.ok(pageOf(pfx+'methods/'+mp+'/').includes('data-fig="reliable-decisions-update.json|'),label+'/methods/'+mp+': route-1 figures reach the method page');
  }
  // Follow-up review of 2026-10-05: the handoff's required limitations go "on any page that shows route-1 results".
  // Every route-1 group on a dataset or method page carries, under its rows and without a figure, its protocol's
  // boundary and the three route-wide limitations that bear on every figure in it (calibration on cross-fit inner
  // models, rejecting errors is not out-of-distribution detection, the difference rule with no multiplicity
  // correction): the export's English verbatim, or the translation table's Chinese; links the rest; and on ds003810
  // calls the contrasts secondary, in the note and on each contrast row.
  {
    const src=stripTypeScriptTypes(readFileSync(new URL('../src/data/reliable-decisions-limits.ts',import.meta.url),'utf8'))
      .replace(/^import[^\n]*\n/gm,'').replace(/^export /gm,'');
    const ctx={reliable:rdx};vm.runInNewContext(src+'\nthis.Z=rdLimitsZh;this.S=rdSecondary;',ctx);
    const digits=s=>[...s.matchAll(/\d[\d,]*(?:\.\d+)?/g)].map(m=>m[0]).sort();
    const shared=['Calibration data are participant-disjoint inner out-of-fold scores','Rejecting likely errors on known classes','A contrast is called a difference only when']
      .map(start=>{const hits=R.boundaries.all_protocols.filter(x=>x.startsWith(start));assert.equal(hits.length,1,'route 1: one limitation starting "'+start+'"');return hits[0];});
    assert.ok(/cross-fit/.test(shared[0])&&/not detecting unfamiliar input/.test(shared[1])&&/no multiplicity correction/.test(shared[2]),'route 1: the three limitations the groups carry');
    const allEn=new Set([...R.boundaries.all_protocols,...Object.values(R.boundaries.per_protocol)]);
    for(const [en,zh] of Object.entries(ctx.Z)){
      assert.ok(allEn.has(en),'reliable-decisions-limits.ts: "'+en.slice(0,50)+'" is no limitation of the export');
      // "Route 1" is 第一条路线 in Chinese, as on the topic page.
      assert.deepEqual(digits(zh),digits(en.replace(/\bRoute 1\b/g,'')),'reliable-decisions-limits.ts: the Chinese for "'+en.slice(0,50)+'" must carry exactly its numbers');
      assert.ok(/\p{Script=Han}/u.test(zh),'reliable-decisions-limits.ts: "'+en.slice(0,50)+'" has no Chinese');
      for(const [bad,good] of Object.entries(rejected)) assert.ok(!hasRejected(zh,bad),`reliable-decisions-limits.ts: "${bad}" is a rejected rendering — use "${good}"`);
    }
    assert.ok(/交叉拟合/.test(ctx.Z[shared[0]])&&/分布外/.test(ctx.Z[shared[1]])&&/不做多重比较校正/.test(ctx.Z[shared[2]]),'reliable-decisions-limits.ts: the Chinese keeps cross-fit, out-of-distribution and no multiplicity correction');
    const protocolOf={eegmat:'arithmetic-rest',beta:'beta-8ch',ds003810:'mi-rest'};
    let groups=0;
    for(const f of htmlPages.filter(f=>/^(?:zh\/)?(?:datasets|methods)\//.test(f))){
      const zh=f.startsWith('zh/'),html=readFileSync(new URL(f,DIST),'utf8');
      for(const [,ds] of html.matchAll(/<section class="entity-group" id="g-(?:([a-z0-9-]+?)-)?reliable-decisions">/g)){
        const slug=ds??f.match(/datasets\/([^/]+)\//)[1],p=protocolOf[slug],where=f+' route-1 group ('+slug+')';
        const g0=html.indexOf(`id="g-${ds?ds+'-':''}reliable-decisions"`),g=html.slice(g0,html.indexOf('</section>',g0));
        const n0=g.indexOf('<p class="protocol-note rd-limits-note"'),note=g.slice(n0,g.indexOf('</p>',n0));
        assert.ok(p&&n0>0&&note.includes(`data-rd-limits="${p}"`),where+': the limitations of its protocol under its rows');
        assert.ok(!/data-fig=/.test(note),where+': the limitations carry no figure');
        // A URL in the text is linked as itself, and nothing after it joins the link (the Chinese did, once).
        const urls=[...note.matchAll(/<a href="(https:[^"]*)"[^>]*>([^<]*)<\/a>/g)];
        assert.ok(urls.length===1&&urls.every(([,h,t])=>h===t&&/^https:\/\/[!-~]+$/.test(h)&&R.literature.some(l=>l.url===h)),where+': the out-of-distribution source is linked as itself ('+urls.map(u=>u[1]).join(' ')+')');
        const text=decodeHtml(note.replace(/<[^>]+>/g,'')).replace(/\s+/g,' ');
        const want=[R.boundaries.per_protocol[p],...shared].map(x=>zh?ctx.Z[x]:x);
        for(const x of want) assert.ok(x&&text.includes(x.replace(/\s+/g,' ')),where+': "'+String(x).slice(0,60)+'"');
        assert.ok(note.includes(`href="${zh?'/zh':''}/topics/when-not-to-act/#rd-limits"`),where+': links every limitation of route 1');
        if(p==='mi-rest'){
          assert.ok(text.includes(zh?ctx.S.zh:ctx.S.en)&&(zh?/次要对比/:/secondary/).test(ctx.S[zh?'zh':'en']),where+': the contrasts are called secondary');
          const c2=[...g.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(m=>m[1]).filter(r=>/Learned reject option|可学习的拒识选项/.test(r));
          assert.ok(c2.length>0&&c2.every(r=>(zh?/（次要对比）/:/\(a secondary contrast\)/).test(r)),where+': each contrast row says it is secondary');
        }else assert.ok(!(zh?/次要对比/:/secondary contrast/).test(g),where+': a primary protocol\'s contrasts are not called secondary');
        groups++;
      }
    }
    assert.equal(groups,2*10,'route-1 groups with their limitations: three dataset pages and seven method-page groups, in both languages');
  }
  // Markup, releases and data use.
  {
    const node=ldOf(pageOf('topics/when-not-to-act/'))[0]['@graph'].find(n=>n['@type']==='Dataset');
    assert.ok(node.distribution.some(d=>d.contentUrl==='https://bci.report/data/reliable-decisions-update.json')&&node.variableMeasured.includes('selective_coverage'),'when-not-to-act: Dataset markup names the route-1 file and what it measures');
    for(const path of ['releases/','zh/releases/']) assert.ok(pageOf(path).includes(`id="${rdx.release_id}"`)&&pageOf(path).includes(rdx.provenance.manifest_sha256),path+': the route-1 release and its manifest');
    const du=pageOf('data-use/'),s0=du.slice(du.indexOf('id="sources-2026-10-04"'),du.indexOf('</section>',du.indexOf('id="sources-2026-10-04"')));
    assert.ok(s0.length>800&&['EEGMAT','BETA','ds003810','BNCI2015-001','idle'].every(x=>s0.includes(x)),'data-use: the 4 October section names its recordings and what is left out');
    // The same date's v9 review has its own entry (review of 2026-10-05): the route-1 sentence is scoped to route 1;
    // each core protocol's reused 2026-09-20 rights record carries its v9 scope, verbatim; each model family's weights
    // terms carry every checkpoint with its revision (REVE's named versions included), the licence note and the owner's
    // decision, verbatim; and the terms that oblige — REVE's licence, LUNA's no-derivatives and no-endorsement, ERP-FM's
    // non-commercial terms, ZUNA 1.1's research use — are stated in the entry's own words.
    assert.ok(s0.includes('Route 1 adds no new dataset and no new model')&&!/<p>Under its own manifest\. No new dataset and no new model/.test(s0),'data-use: "no new model" is scoped to route 1');
    // Follow-up review of 2026-10-05: the file said it carried no ds003810 figure but the coverage and the learned-reject
    // contrasts, while it carries the accuracy, the error accepting everything, the selective error at the fixed
    // threshold and the certified-risk counts. not_published names what is withheld, the file carries none of it, and
    // the privacy review (printed in data use's ds003810 row) lists what is published.
    {
      const item=rdx.not_published.filter(x=>x.startsWith('On ds003810'));
      assert.ok(item.length===1&&!rdx.not_published.some(x=>/every ds003810 figure other than/.test(x)),'route 1: not_published names what ds003810 withholds, not "every figure other than"');
      const withheld={'the coverage-target rule':'coverage_target','the two rankings':'ranking_S','probability quality':'probability_quality','recalibration':'recalibration'};
      for(const [words,key] of Object.entries(withheld)) assert.ok(item[0].includes(words)&&M.methods.every(m=>!(key in m)),'route 1: ds003810 withholds '+words+', and the file carries none');
      assert.ok(R.robustness.seeds.rows.every(r=>r.protocol!=='mi-rest'),'route 1: no ds003810 secondary seed in the file');
      const pr=M.rights.privacyReview,row=s0.slice(s0.lastIndexOf('<tr',s0.indexOf(escHtml(pr))),s0.indexOf('</tr>',s0.indexOf(escHtml(pr))));
      assert.ok(s0.includes(escHtml(pr))&&row.includes('ds003810'),'data-use: the ds003810 row prints its privacy review');
      const lists={'the published balanced accuracy':'balanced_accuracy','the error when everything is accepted':'error_accepting_everything','the selective error':'fixed_cutoff','flagged unstable':'fixed_cutoff','had nothing accepted':'fixed_cutoff','the learned-reject contrasts':'learned_minus_confidence','the certified-risk rule\'s settings (delta and target) and fold counts':'risk_certification'};
      for(const [words,key] of Object.entries(lists)) assert.ok(pr.includes(words)&&M.methods.every(m=>key in m),'data-use: the ds003810 row lists '+words+', which the file carries');
      assert.deepEqual(M.methods.map(m=>Object.keys(m).join()),M.methods.map(()=>'id,label,seed,balanced_accuracy,site_value,error_accepting_everything,fixed_cutoff,learned_minus_confidence,risk_certification'),'route 1: ds003810 carries exactly what its privacy review lists');
      // Second follow-up review of 2026-10-05: the nested fields too. Under the fixed threshold each method carries a
      // whole-person bootstrap interval for its coverage and, where something was accepted, for its selective error;
      // the certified-risk block carries the rule's settings and what accepting nothing leaves. The review names both,
      // and the file carries exactly these fields, in this order.
      assert.ok(pr.includes('pooled coverage and the selective error (a count of wrong among accepted, flagged unstable, where fewer than ten were accepted), each with its whole-person bootstrap interval where defined'),'data-use: the ds003810 row names the fixed threshold\'s intervals');
      assert.ok(pr.includes('with nothing accepted: a coverage of zero, all ten people with nothing accepted, and so no error and no error relative to the target'),'data-use: the ds003810 row says the certified-risk rule accepted nothing');
      const fixedSome='cutoff,n,accepted,coverage,coverage_interval_95,selective_error,accepted_wrong,unstable,selective_error_interval_95,people_with_nothing_accepted';
      const fixedNone='cutoff,n,accepted,coverage,coverage_interval_95,selective_error,selective_error_status,unstable,people_with_nothing_accepted';
      const riskNone='delta,target,outer_folds,certified_folds,folds_over_target,n,accepted,coverage,selective_error,selective_error_status,unstable,people_with_nothing_accepted,target_weighted,error_minus_target,error_minus_target_status';
      for(const m of M.methods){
        const f=m.fixed_cutoff,r=m.risk_certification;
        assert.equal(Object.keys(f).join(),f.accepted>0?fixedSome:fixedNone,'route 1: ds003810 '+m.id+': the fixed threshold carries exactly what the review lists');
        assert.equal(Object.keys(r).join(),riskNone,'route 1: ds003810 '+m.id+': the certified-risk block carries exactly what the review lists');
        assert.ok(r.accepted===0&&r.coverage===0&&r.people_with_nothing_accepted===M.people&&M.people===10&&r.selective_error===null&&r.error_minus_target===null&&r.target_weighted===null,'route 1: ds003810 '+m.id+': the certified-risk rule accepted nothing, as the review says');
        for(const [k,c] of Object.entries(m.learned_minus_confidence)) assert.equal(Object.keys(c).join(),'mean,interval_95,excludes_zero','route 1: ds003810 '+m.id+': the contrast '+k+' carries its mean and whole-person interval');
        assert.deepEqual(Object.keys(m.learned_minus_confidence),['aurc','error_at_80'],'route 1: ds003810 '+m.id+': the two learned-reject contrasts');
      }
    }
    const F9=JSON.parse(readFileSync(new URL('data/foundation-models-update.json',DIST),'utf8')).results['foundation-models-v9'];
    const at9=s0.indexOf('<h3 id="sources-2026-10-04-v9">'),v9=s0.slice(at9);
    assert.ok(at9>0&&at9>s0.indexOf('<h3 id="sources-2026-10-04-route-1">'),'data-use: the v9 review is its own entry under 4 October, after route 1');
    const e9=x=>escHtml(x);
    assert.deepEqual([...v9.matchAll(/<tr data-v9-source="([^"]+)">/g)].map(m=>m[1]),F9.protocols.map(p=>p.id),'data-use: one v9 rights row per core protocol, in the matrix order');
    for(const p of F9.protocols){
      const r=v9.slice(v9.indexOf(`<tr data-v9-source="${p.id}">`),v9.indexOf('</tr>',v9.indexOf(`<tr data-v9-source="${p.id}">`)));
      assert.ok(r.includes(e9(p.rights.privacyReview))&&/Reused unchanged from the 2026-09-20 review/.test(p.rights.privacyReview)&&/Published here:/.test(p.rights.privacyReview),'data-use: '+p.id+' carries its reused rights record and v9 scope');
      assert.ok(r.includes(`href="${e9(p.rights.source)}"`)&&r.includes(`href="${e9(p.rights.licenseUrl)}"`)&&r.includes(`href="/protocols/${p.id}/#foundation-v9"`),'data-use: '+p.id+' links its source, licence and v9 rows');
    }
    const lic9=[...v9.matchAll(/<tr data-v9-licence="([^"]+)">([\s\S]*?)<\/tr>/g)];
    for(const m of F9.models){
      const r=lic9.find(x=>x[2].includes('<span>'+e9(m.name)+'</span>'));
      assert.ok(r,'data-use: '+m.name+' is listed with the weights terms');
      assert.ok(m.revision?r[2].includes('<code>'+e9(m.revision)+'</code>'):r[2].includes('revision not in the release'),'data-use: '+m.name+' with its revision');
      // A revision that is only a file id names its SHA-256 as the identity: the hash is printed beside it (review of 2026-10-05).
      if(/sha256 is the identity/.test(m.revision??'')) assert.ok(m.checkpoint_sha256&&r[2].includes('<code>'+e9(m.revision)+'</code> · SHA-256 <code>'+m.checkpoint_sha256+'</code>'),'data-use: '+m.name+' with the SHA-256 its revision names as its identity');
      assert.ok(r[2].includes(e9(m.rights_review)),'data-use: '+m.name+' with the owner\'s review of its weights');
      if(!/\(as /.test(m.licence_note)) assert.ok(r[2].includes(e9(m.licence_note)),'data-use: '+m.name+' with its licence note');
    }
    for(const rev of F9.models.filter(m=>m.id.startsWith('reve-')).map(m=>m.revision)) assert.ok(v9.includes(e9(rev)),'data-use: REVE named by version ('+rev+')');
    const v9t=visible(v9);
    for(const re of [/REVE Responsible Use License, accepted by the owner/,/LUNA’s CC BY-ND 4\.0[^.]*no endorsement implied/,/ERP-FM’s CC BY-NC-SA 4\.0, non-commercial/,/ZUNA 1\.1’s model card, research use only, not for diagnosis or clinical use/,
                     /no model’s authors endorse these results/,/not proof that a recording was never seen/,/pinned by hash in the review manifest/,/timings and memory/])
      assert.match(v9t,re,'data-use: the v9 entry states '+re);
    assert.ok(v9.includes('href="/releases/#foundation-models-update-20261004"'),'data-use: the v9 entry links its release');
  }
}
// --- 2026-10-04 v9 foundation models: the publication boundary ---------------------------------
// Eleven further foundation models (sixteen encoder checkpoints) as frozen probes on the eight core
// protocols, nine adapted on EEGMAT (owner approval 2026-10-04). The batch ships one JSON and a CSV
// per protocol; the released matrix keeps its bytes. Read from dist/ so a hand-edited build is
// caught. Pinned here: the files are the reviewed ones and agree with each other; each CSV starts
// with its core results CSV's columns and protocol values, one row per checkpoint, matrix rows
// before the masking ablation; a cell not run is empty with its reason, never 0; the chance flag
// follows the interval; exposure is the owner's sourced statement — never "not exposed" or a proof
// — with ST-EEGFormer on BETA and SingLEM on TMNRED in the list, ZUNA 1.1 unknown everywhere, and
// LaBraM and CBraMod absent from their authors' lists, each with a source link; ZUNA 1.1's
// research-use sentence travels with its rows; no timing is published; the release log names the
// batch and its manifest.
{
  const served=f=>readFileSync(new URL('data/'+f,DIST));
  assert.deepEqual(served('foundation-models-update.json'),readFileSync(new URL('../src/data/foundation-models-update.json',import.meta.url)),
    'source and served foundation-model exports must be byte-identical');
  const fm=JSON.parse(served('foundation-models-update.json')),F=fm.results['foundation-models-v9'];
  assert.deepEqual(Object.keys(fm.results),['foundation-models-v9'],'one result, the v9 evaluation');
  assert.deepEqual([fm.status_only,fm.holds],[[],[]],'the v9 batch has no status-only source and no hold');
  const protocols=data.tracks.map(t=>t.id);
  assert.deepEqual(F.protocols.map(p=>p.id),protocols,'the v9 rows cover the eight core protocols, in the matrix order');
  const panel=k=>F.models.filter(m=>m.panel===k).map(m=>m.id);
  assert.deepEqual([F.models.length,panel('matrix').length,panel('masking ablation').length,F.models.filter(m=>m.masking_ablation).length],[16,13,3,4],
    'sixteen checkpoints: thirteen matrix rows and three ablation siblings of the fourth masking checkpoint');
  assert.deepEqual(F.models.map(m=>m.id),[...panel('matrix'),...panel('masking ablation')],'matrix rows before the masking ablation');
  // The released matrix is not edited: no v9 row reaches experiments.json (REVE Base stays in its directory).
  const releasedRows=JSON.parse(served('experiments.json')).tracks.flatMap(t=>t.rows.map(r=>r.name));
  for(const m of F.models) assert.ok(!releasedRows.includes(m.name),m.name+': a v9 row reached the released matrix');
  const cell=(m,p)=>F.frozen_probe.find(c=>c.model===m&&c.protocol===p);
  assert.equal(F.frozen_probe.length,16*8,'one cell per checkpoint and protocol');
  const notRun=F.frozen_probe.filter(c=>c.status!=='complete');
  assert.deepEqual(notRun.map(c=>c.model+' '+c.protocol).sort(),['brainomni-base p300-target','brainomni-base semantic-target'],'two cells not run');
  assert.ok(notRun.every(c=>c.balanced_accuracy===null&&c.reason.length>40),'a cell not run is null with its reason, never zero');
  // Exposure: a sourced statement, never a proof.
  const E=F.pretraining_exposure,S=E.statements;
  assert.equal(S.not_exposed,"not in the authors' published pretraining list (checked 2026-10-04)",'the owner\'s wording for a dataset absent from the list');
  assert.ok(Object.values(S).every(x=>!/proven|no overlap|not exposed|guarantee/i.test(x)),'exposure statements never claim proof');
  const exposed=F.frozen_probe.filter(c=>c.exposure.status==='exposed').map(c=>c.model+' '+c.protocol).sort();
  assert.deepEqual(exposed,['singlem semantic-target','steegformer-base beta-4ch','steegformer-base beta-8ch','steegformer-large beta-4ch','steegformer-large beta-8ch'],'the exposed cells');
  assert.ok(F.frozen_probe.every(c=>(c.model==='zuna')===(c.exposure.status==='unknown')),'every ZUNA 1.1 cell, and only those, unknown');
  assert.ok(F.frozen_probe.every(c=>c.exposure.statement===S[c.exposure.status]),'every cell carries its statement');
  for(const k of ['labram','cbramod']){
    const rows=E.cells.filter(c=>c.model===k);
    assert.ok(rows.length===7&&rows.every(c=>c.status==='not_exposed'&&c.statement===S.not_exposed&&c.urls.length&&c.urls.every(u=>u.startsWith('https://'))),
      k+': every core dataset absent from the authors\' published list, with the source');
  }
  const zuna=F.models.find(m=>m.id==='zuna');
  assert.match(zuna.licence_note,/research use only, not for diagnosis or clinical use/,'ZUNA 1.1: the model card\'s research-use sentence');
  // Review of 2026-10-05: the candidate's "EEGMamba not exposed at medium confidence" and "user-approved" are restated
  // in the owner's wording, in the JSON and every CSV; the exposure limitation reads the authors' lists.
  {const text=served('foundation-models-update.json').toString()+protocols.map(p=>served('foundation-models-'+p+'.csv').toString()).join('');
   assert.ok(!/not exposed/i.test(text)&&!text.includes('user-approved'),'the v9 files say neither "not exposed" nor "user-approved"');
   const lim=F.required_limitations.filter(x=>/^Pretraining exposure/.test(x));
   assert.ok(lim.length===1&&/published pretraining lists show it \(checked 2026-10-04\)/.test(lim[0])&&/not proof/.test(lim[0]),'the exposure limitation is the authors\' lists, not a proof');
   assert.match(E.wording_rule,/confidence rates how closely its source enumerates the corpus/,'the exposure confidence is said to rate the source, not the absence of overlap');}
  // Review of 2026-10-05: the candidate stated each REVE sensitivity run as primary minus sensitivity ("changes P300 by
  // -0.71"), so every sign read backwards. The export restates both footnotes from the aggregate's balanced accuracies
  // (REVE Base without mean removal: P300 up, sleep down; Large: both down) and the notes say the run is stated in the
  // row footnote, the only place it is published. The sizes and directions are pinned here because the run's scores
  // are not in any served file.
  {const text=served('foundation-models-update.json').toString()+protocols.map(p=>served('foundation-models-'+p+'.csv').toString()).join('');
   assert.ok(!/changes P300 by|reported separately/.test(text),'the v9 files state no sensitivity run as a signed "change" and none as "reported separately"');
   const want={'reve-base':'a no-mean-removal sensitivity run scores P300 0.71 percentage points higher and sleep 1.40 lower.',
               'reve-large':'the no-mean-removal sensitivity run scores P300 2.06 percentage points lower and sleep 0.93 lower.'};
   assert.deepEqual(F.models.filter(m=>/sensitivity run/.test(m.row_footnote)).map(m=>m.id),Object.keys(want),'only the REVE footnotes state a sensitivity run');
   for(const [k,s] of Object.entries(want)){
     const m=F.models.find(x=>x.id===k);
     assert.ok(m.row_footnote.endsWith(s),k+': the footnote states the sensitivity run in the direction the aggregate gives ("'+s+'")');
     assert.ok(m.notes.some(n=>n.endsWith('; a no-mean-removal sensitivity run is stated in the row footnote.')),k+': the note says where the sensitivity run is stated');
     for(const p of protocols){const [head,...body]=csvRows(served('foundation-models-'+p+'.csv').toString()),r=body.find(x=>x[head.indexOf('model_id')]===k);
       assert.ok(r[head.indexOf('row_footnote')]===m.row_footnote&&r[head.indexOf('notes')].includes('stated in the row footnote'),p+'/'+k+': the CSV carries the restated footnote and note');}
   }}
  // Each protocol's CSV against the JSON and its core results CSV.
  for(const p of protocols){
    const rows=csvRows(served('foundation-models-'+p+'.csv').toString()),core=csvRows(served(p+'-results.csv').toString());
    const [head,...body]=rows,col=k=>head.indexOf(k);
    assert.deepEqual(head.slice(0,core[0].length),core[0],p+': the CSV starts with the core results CSV\'s columns');
    assert.ok(body.every(r=>r.length===head.length),p+': every row fits the header');
    assert.deepEqual(body.map(r=>r[col('model_id')]),F.models.map(m=>m.id),p+': one row per checkpoint, in order');
    for(const k of ['dataset','dataset_version','protocol_id','channels','primary_metric','secondary_metric','chance_level_percent','source','license','license_url','attribution','scope'])
      assert.ok(body.every(r=>r[col(k)]===core[1][core[0].indexOf(k)]),p+': '+k+' is the core protocol\'s');
    for(const r of body){
      const m=F.models.find(x=>x.id===r[col('model_id')]),c=cell(m.id,p),where=p+'/'+m.id;
      assert.equal(r[col('model')],m.name,where+': name');
      assert.equal(r[col('scoring_seconds')],'',where+': timings are not published');
      assert.equal(r[col('pretraining_exposure')],c.exposure.statement,where+': exposure statement');
      assert.equal(r[col('panel')],m.panel,where+': panel');
      if(m.id==='zuna') assert.match(r[col('licence_note')],/research use only, not for diagnosis or clinical use/,where+': research-use sentence');
      if(c.status!=='complete'){
        assert.ok(['primary_percent','secondary_value','descriptive_interval_low_percent','descriptive_interval_high_percent','participants'].every(k=>r[col(k)]==='')&&r[col('not_run_reason')]===c.reason,where+': not run is empty with its reason');
      }else if(p==='idle'){
        assert.ok(Math.abs(Number(r[col('primary_percent')])-100*c.commands_detected/c.command_trials)<1e-9&&Math.abs(Number(r[col('secondary_value')])-100*c.idle_false_activations/c.idle_trials)<1e-9,where+': idle rates are the counts over 60');
        assert.ok(Number(r[col('always_abstain_participants')])===c.always_abstain_people&&r[col('commands_detected')]===String(c.commands_detected),where+': idle counts');
      }else{
        const pc=v=>Number(v);
        assert.ok(Math.abs(pc(r[col('primary_percent')])-100*c.balanced_accuracy)<1e-9&&Math.abs(pc(r[col('descriptive_interval_low_percent')])-100*c.interval_95[0])<1e-9
          &&Math.abs(pc(r[col('descriptive_interval_high_percent')])-100*c.interval_95[1])<1e-9&&Number(r[col('participants')])===c.people,where+': balanced accuracy and interval in percent');
        const chance=data.tracks.find(t=>t.id===p).chanceLevel;
        const includes=pc(r[col('descriptive_interval_low_percent')])<=chance&&chance<=pc(r[col('descriptive_interval_high_percent')]);
        assert.equal(r[col('interval_includes_chance')],String(includes),where+': the chance flag follows the interval');
        assert.equal(c.interval_includes_chance,includes,where+': the JSON chance flag follows the interval');
      }
    }
  }
  for(const path of ['releases/','zh/releases/'])
    assert.ok(pageOf(path).includes(`id="${fm.release_id}"`)&&pageOf(path).includes(fm.provenance.manifest_sha256),path+': the v9 release and its manifest');
  // The API page and the feed list the nine files through the generic checks above (every served file, exactly once).
}
console.log('PASS: 2026-10-04 v9 foundation models, boundary — JSON and eight CSVs served as reviewed and agreeing; the released matrix untouched; each CSV in its core results CSV\'s columns and protocol values, one row per checkpoint, matrix before ablation; not run empty with its reason; chance flags follow the intervals; exposure a sourced statement with LaBraM and CBraMod sourced, ST-EEGFormer×BETA and SingLEM×TMNRED exposed, ZUNA 1.1 unknown; research-use sentence; no timings; release log.');
// --- 2026-10-07 route 2, one representation and several questions: the publication boundary -----
// A shared encoder with fixed heads against a question-conditioned head and separate models, at matched
// data and compute (owner approvals of 2026-10-06 and 2026-10-07). One JSON, registered (release log,
// feed, API page, home Dataset markup, data use) before any page prints it; the page comes in a later
// commit. Read from dist/ so a hand-edited build is caught. Pinned here: the served file is the
// reviewed one; one result, no status-only source and no hold; OpenBMI, BOAS and EESM19 in that order;
// 21 primary entries; every flag and wording follows its interval and the 2-pp margin (log 0.8 for P3
// and S4); every contrast is the difference of its arms; every gate follows its arm's interval; each
// route sentence follows its counted questions, and a floor-gated question is never counted; every
// secondary entry carries its gate and who attached it, S2 at Level 1 labelled as the audit's; E2 sleep
// carries its disclosure, one seed, its own gates and no checkpoint left; BOAS carries its three gaps,
// its attribution and "pseudonymised", in the file, its rights record, the release log and data use,
// every BOAS cell pools at least 20 people, and no per-person percentile is a key anywhere in the file.
{
  const served=f=>readFileSync(new URL('data/'+f,DIST));
  assert.deepEqual(served('shared-representation-update.json'),readFileSync(new URL('../src/data/shared-representation-update.json',import.meta.url)),
    'source and served route-2 exports must be byte-identical');
  const sr=JSON.parse(served('shared-representation-update.json')),R2=sr.results['one-representation'];
  assert.deepEqual(Object.keys(sr.results),['one-representation'],'route 2: one result');
  assert.deepEqual([sr.status_only,sr.holds],[[],[]],'route 2: no status-only source and no hold');
  const D=R2.datasets;
  assert.deepEqual(Object.keys(D),['openbmi','boas','eesm19'],'route 2: OpenBMI and BOAS primary, EESM19 a crude replication');
  assert.ok(D.eesm19.role==='secondary, crude'&&D.eesm19.seeds===1&&D.eesm19.secondary.every(e=>e.single_seed&&e.label==='crude (20 people), one seed'),'route 2: EESM19 is crude and one seed');
  assert.equal([...D.openbmi.entries,...D.boas.entries].filter(e=>e.role==='primary').length,21,'route 2: 21 pre-declared primary entries');
  const DELTA=R2.design.margin.delta_pp,L08=Math.log(0.8);
  assert.equal(DELTA,2,'route 2: the margin fixed at the freeze');
  const upper=new Set(['P1','P4','P5','S1','S2','S3-P1','S3-P5','S5','S6-P1','S7','S8','S13-P1','S14','X1']);
  const lower=new Set(['P2','S3-P2','S6-P2','S10','S12','S12-P2','S13-P2']);
  const all=Object.values(D).flatMap(d=>[...(d.entries??[]),...(d.secondary??[]),...(d.e2_sleep?.entries??[])]);
  for(const e of all){
    const w=`route 2: ${e.id} ${e.level} ${e.question}`;
    if('log_r' in e){
      const [lo,hi]=e.interval_95;
      assert.ok(lo<=e.log_r&&e.log_r<=hi,w+': the interval holds its point');
      const diff=hi<0?'difference: dedicated model leaves less error':lo>0?'difference: read-out leaves less error':'no difference shown';
      const margin=L08<lo&&hi<-L08?'equivalent within delta':lo>L08?'non-inferior':'margin not met';
      assert.deepEqual([e.difference,e.margin],[diff,margin],w+': the flags follow the interval and log 0.8');
      assert.ok(Math.abs(Math.log(e.r)-e.log_r)<1e-9&&Math.abs((1-e.auroc.dedicated)/(1-e.auroc.read_out)-e.r)<1e-9,w+': R is the ratio of remaining errors');
      assert.equal(e.gate,e.read_out_auroc_interval_95[0]>0.55?'pass':'floor',w+': the gate follows the read-out\'s AUROC interval');
    }else if('estimate_pp' in e){
      const [lo,hi]=e.interval_95_pp;
      assert.ok(lo<=e.estimate_pp&&e.estimate_pp<=hi,w+': the interval holds its point');
      assert.equal(e.difference.startsWith('difference: '),lo>0||hi<0,w+': the difference flag follows the interval');
      assert.ok(e.id==='S11'||upper.has(e.id)||lower.has(e.id),w+': a margin rule');
      const margin=e.id==='S11'?'not applicable (descriptive contrast)':-DELTA<lo&&hi<DELTA?'equivalent within delta'
        :(upper.has(e.id)?hi<DELTA:lo>-DELTA)?'non-inferior':'margin not met';
      assert.equal(e.margin,margin,w+': the margin flag follows the interval and the 2-pp margin');
      assert.equal(e.wording,e.difference==='no difference shown'&&e.margin==='margin not met'?'inconclusive at this sample size':e.difference+'; '+e.margin,w+': the wording follows the flags');
      const [x,y]=Object.values(e.mean_balanced_accuracy);
      assert.ok(Math.abs(100*(x-y)-e.estimate_pp)<1e-9,w+': the contrast is the difference of its arms');
      assert.equal(e.per_seed.length,e.single_seed?0:3,w+': per-seed points only with three seeds');
    }
    if(e.role!=='primary') assert.ok(e.gate&&e.gate_attached_by,w+': a gate label and who attached it');
  }
  for(const d of [D.openbmi,D.boas]){
    for(const g of d.gates) assert.equal(g.gate,g.interval_95[0]<=g.chance+0.05?'floor':g.interval_95[1]>=0.95?'ceiling: equivalence uninformative':'pass',`route 2: ${d.dataset} ${g.level} ${g.question}: the gate follows the arm's interval`);
    const p1=d.entries.filter(e=>e.id==='P1'),rs=d.route_sentence,counted=p1.filter(e=>e.gate==='pass').map(e=>e.question);
    assert.deepEqual(rs.counted,counted,`route 2: ${d.dataset}: the route sentence counts the questions that pass their gate`);
    assert.deepEqual(Object.keys(rs.excluded),p1.filter(e=>e.gate!=='pass').map(e=>e.question),`route 2: ${d.dataset}: the questions it leaves out`);
    const met=counted.every(q=>['equivalent within delta','non-inferior'].includes(p1.find(e=>e.question===q).margin));
    assert.ok(rs.supported===(counted.length>0&&met&&rs.fixed_heads_for_less)&&(rs.sentence==='The fixed-heads sentence is not supported')===!rs.supported,`route 2: ${d.dataset}: the route sentence follows its counted questions and the ledger`);
    for(const e of d.entries.filter(e=>e.role==='primary'&&e.gate!=='pass')) assert.deepEqual(e.sentences_derived_by_audit,[],`route 2: ${d.dataset} ${e.id} ${e.question}: a floor-gated entry is never counted`);
  }
  const s2=all.filter(e=>e.id==='S2'&&e.level==='L1');
  assert.ok(s2.length===5&&s2.every(e=>/independent secondary audit/.test(e.computed_by)),'route 2: S2 at Level 1 labelled as computed by the independent audit');
  const E2=D.boas.e2_sleep;
  assert.ok(E2.run_after_other_results===true&&/after every other primary and secondary result/.test(E2.disclosure)&&/fixed at the freeze/.test(E2.disclosure)
    &&E2.resume_checkpoints.left_after_the_run===0&&E2.seeds===1&&E2.entries.length===9
    &&E2.entries.every(e=>e.single_seed&&e.gate===E2.gates.find(g=>g.question===e.question).gate),'route 2: E2 sleep with its disclosure, one seed, its own gates and no checkpoint left');
  // BOAS: the owner's conditions.
  const C=R2.boas_conditions,B=D.boas.rights;
  assert.ok(C.gaps.length===3&&JSON.stringify(B.gaps)===JSON.stringify(C.gaps)&&B.attribution===C.attribution&&C.participants==='pseudonymised in the public release'&&B.participants===C.participants,
    'route 2: BOAS carries its three gaps, its attribution and "pseudonymised" in the file and its rights record');
  assert.ok(C.owner_approval.approved_on==='2026-10-07'&&C.owner_approval.decision==='publishable with stated gaps','route 2: the BOAS approval');
  const peopleIn=v=>Array.isArray(v)?v.flatMap(peopleIn):v&&typeof v==='object'?Object.entries(v).flatMap(([k,x])=>['included_people','people','training_people'].includes(k)&&Number.isInteger(x)?[x]:peopleIn(x)):[];
  const boasPeople=peopleIn(D.boas);
  assert.ok(boasPeople.length>100&&Math.min(...boasPeople)>=C.minimum_cell_people&&C.minimum_cell_people===20&&Math.min(...boasPeople)===C.smallest_cell_people,'route 2: every BOAS cell pools at least 20 people');
  assert.doesNotMatch(served('shared-representation-update.json').toString(),/"(?:p[159]0(?:_pp)?|[^"]*percentile[^"]*|[^"]*per_person[^"]*|[^"]*per_fold[^"]*)":/,'route 2: no per-person percentile or per-fold value in the file');
  for(const path of ['releases/','zh/releases/']) assert.ok(pageOf(path).includes(`id="${sr.release_id}"`)&&pageOf(path).includes(sr.provenance.manifest_sha256),path+': the route-2 release and its manifest');
  {const rel=pageOf('releases/'),at=rel.indexOf(`id="${sr.release_id}"`),entry=visible(rel.slice(at,rel.indexOf('</article>',at)));
   for(const re of [/publishable with stated gaps/,/public sharing or secondary use/,/no peer-reviewed paper describes BOAS/i,/version 1\.1\.1 \(May 2025\)/,/pseudonymised in the public release/,/after every other result was known/])
     assert.match(entry,re,'releases: the route-2 entry states '+re);}
  // Data use: the three records, each ending with what route 2 publishes; BOAS's gaps and credit in full.
  const du=pageOf('data-use/'),at7=du.indexOf('id="sources-2026-10-07"'),s7=du.slice(at7,du.indexOf('</section>',at7));
  assert.deepEqual([...s7.matchAll(/<tr data-route2-source="([^"]+)">/g)].map(m=>m[1]),['openbmi','boas','eesm19'],'data-use: one route-2 rights row per dataset');
  for(const id of ['openbmi','boas','eesm19']){
    const r=D[id].rights,row=s7.slice(s7.indexOf(`<tr data-route2-source="${id}">`),s7.indexOf('</tr>',s7.indexOf(`<tr data-route2-source="${id}">`)));
    assert.ok(row.includes(escHtml(r.privacyReview))&&row.includes(escHtml(r.attribution))&&row.includes(`href="${escHtml(r.source)}"`)&&row.includes(`href="${escHtml(r.licenseUrl)}"`),'data-use: '+id+' prints its rights record');
    assert.ok(id==='boas'?/Published here: /.test(r.privacyReview):/Reused unchanged from the 2026-\d\d-\d\d review[^.]*\. Published here for route 2[,:] /.test(r.privacyReview),'data-use: '+id+' says what route 2 publishes');
  }
  // The BOAS paragraph itself (the table rows carry the attribution too): the three gaps, the credit and the wording.
  {const gp=s7.indexOf('<p id="boas-gaps">'),t=visible(s7.slice(gp,s7.indexOf('</p>',gp)));
   assert.ok(gp>0,'data-use: the BOAS paragraph');
   for(const x of [...C.gaps,C.attribution,'Participants are pseudonymised in the public release.',C.not_an_evaluation_of]) assert.ok(t.includes(x),'data-use: the BOAS entry states "'+x.slice(0,50)+'"');}
  assert.ok(s7.includes(`href="/releases/#${sr.release_id}"`),'data-use: the route-2 entry links its release');
}
console.log('PASS: 2026-10-07 route 2, boundary — served as reviewed; OpenBMI, BOAS and EESM19 (crude, one seed); 21 primary entries; every flag, wording and gate follows its interval and the frozen margin; contrasts are their arms\' differences; route sentences from the counted questions, floor never counted; secondary gates with who attached them, S2 at Level 1 the audit\'s; E2 sleep disclosed with no checkpoint left; BOAS gaps, credit and "pseudonymised" in the file, the release log and data use; no BOAS cell under 20 people; no per-person percentile.');
// --- 2026-10-07 route 2 on the site: one model, several questions --------------------------------------------
// The route's own question, /topics/shared-encoder/ (owner approval 2026-10-07; the roadmap on when-not-to-act marks
// it run, checked with the roadmap above), the BOAS dataset page and register entry, and route-2 groups on the
// OpenBMI, BOAS and EESM19 pages and, through them, the EEGNet and CBraMod pages. Every figure there is a data-fig
// re-read from the export by the loops above; pinned here is what travels with those figures. Every contrast row
// prints the export's two flags in words: the arm its interval favours (or no difference shown), the margin with
// its 2 pp (20% for log R), "inconclusive" exactly where the export says so; a floor-gated row says the margin is not
// read and the entry is not counted; a secondary row says who attached its gate, S2 on frozen features that the
// audit computed it. Every BOAS figure, on any page, lies in an element marked data-boas that holds the three gaps,
// the credit and "pseudonymised in the public release"; the short answer, the description and the cards print none.
// The route verdicts follow the export's route sentences; E2 sleep carries its disclosure; EESM19 is crude, one seed,
// with the stage sentence; SL-E and SL-F sit beside the stage-only read-out; the secondary panel is collapsed; every
// required limitation is printed in the page's language, and the Chinese carries exactly the English's numbers.
{
  const SRF='shared-representation-update.json';
  const sr=JSON.parse(readFileSync(new URL('data/'+SRF,DIST),'utf8')),R=sr.results['one-representation'],DS=R.datasets,E2=DS.boas.e2_sleep;
  const DELTA=R.design.margin.delta_pp,CUT=Math.round(R.design.margin.p3_min_error_removed*100);
  // The Chinese the pages print for the export's English, read from the module that prints it (shared-encoder.ts).
  const SRZ=(()=>{const c={shared:sr};vm.runInNewContext(stripTypeScriptTypes(readFileSync(new URL('../src/data/shared-encoder.ts',import.meta.url),'utf8'))
    .replace(/^import[^\n]*\n/gm,'').replace(/^export /gm,'')+'\nthis.srZh=srZh;',c);return c.srZh;})();
  const noMonth=t=>t.replace(/(\d{4}) 年 \d{1,2} 月/g,'$1');
  for(const [en,zh] of Object.entries(SRZ))
    assert.deepEqual(numbers(noMonth(zh)).map(n=>n.replace(/,$/,'')).sort(),numbers(en).map(n=>n.replace(/,$/,'')).sort(),'shared-encoder.ts: the Chinese of "'+en.slice(0,60)+'" carries exactly its numbers');
  const required=[...R.boundaries.protocol,...R.boundaries.added];
  for(const en of [...required,...R.boas_conditions.gaps,R.boas_conditions.not_an_evaluation_of,...R.not_run.flatMap(x=>[x.arm,x.status]),...R.not_reported.flatMap(x=>[x.item,x.status])])
    assert.ok(typeof SRZ[en]==='string','shared-encoder.ts: a Chinese text for "'+en.slice(0,60)+'"');
  // Words, written here independently of the page module.
  const codeIn=(c,zh)=>{const s=c.match(/^A_([A-Z]{2}-[A-Z])\(step-matched\)$/);if(s)return zh?`A(${s[1]})，步数匹配`:`A(${s[1]}), step-matched`;
    const a=c.match(/^A_([A-Z]{2}-[A-Z])$/);return a?`A(${a[1]})`:c;};
  const diffWords=(e,zh)=>{
    if('log_r' in e){const [lo,hi]=e.interval_95;return !(lo>0||hi<0)?(zh?'未显示差异':'No difference shown'):hi<0?(zh?'专用模型剩余的错误更少':'Dedicated model leaves less error'):(zh?'读出剩余的错误更少':'Read-out leaves less error');}
    const [lo,hi]=e.interval_95_pp;
    if(!(lo>0||hi<0)) return zh?'未显示差异':'No difference shown';
    if(/^readout\[/.test(e.y)) return e.estimate_pp>0?(zh?'专用分类头更高':'Dedicated head higher'):(zh?'由分期概率读出的更高':'Read-out from the stage probabilities higher');
    const who=codeIn(e.estimate_pp>0?e.x:e.y,zh);return zh?who+' 更高':who+' higher';};
  // A non-inferior flag names the arm it clears (review of 2026-10-07: "Non-inferior at 2 pp" left readers to take the
  // first-named arm, which on P5 SL-A is the wrong one). By the frozen rule (the protocol's decision_rules.flags, as
  // the export check above has it): where the upper bound decides, x − y below +2 pp clears y; where the lower bound
  // decides, above −2 pp clears x; for log R the dedicated model is shown not to cut 20% of the read-out's error.
  const UPPER_BOUND=new Set(['P1','P4','P5','S1','S2','S3-P1','S3-P5','S5','S6-P1','S7','S8','S13-P1','S14','X1']);
  const niWho=(e,zh)=>'log_r' in e?(zh?'读出':'Read-out'):codeIn(UPPER_BOUND.has(e.id)?e.y:e.x,zh);
  const marginWords=(e,zh)=>{const logr='log_r' in e;return ({
    'equivalent within delta':logr?(zh?`在 ${CUT}% 界值内等效`:`Equivalent within the ${CUT}% margin`):(zh?`在 ±${DELTA} pp 内等效`:`Equivalent within ±${DELTA} pp`),
    'non-inferior':logr?(zh?`读出非劣（界值 ${CUT}%）`:`Read-out non-inferior at ${CUT}%`):(zh?`${niWho(e,zh)} 非劣（界值 ${DELTA} pp）`:`${niWho(e,zh)} non-inferior at ${DELTA} pp`),
    'margin not met':logr?(zh?`未达到 ${CUT}% 界值`:`${CUT}% margin not met`):(zh?`未达到 ${DELTA} pp 界值`:`${DELTA} pp margin not met`),
    'not applicable (descriptive contrast)':zh?'描述性对比，不设界值':'No margin: a descriptive contrast'})[e.margin];};
  const gateWords=(g,zh)=>({pass:zh?'通过门槛':'Gate passed',floor:zh?'处于下限：报告，不计入':'At floor: reported, not counted','not applicable':zh?'不适用：描述性':'No gate: descriptive'})[g];
  const byWords=(b,zh)=>({'independent secondary audit':zh?'由独立的次要审计附上':'attached by the independent secondary audit',run:zh?'由运行本身附上':'attached by the run',
    'level gate':zh?'所在层级的门槛':'the level’s gate','E2-sleep scorer, recomputed by its independent audit':zh?'由 E2 睡眠评分程序附上，并经其审计重算':'attached by the E2-sleep scorer, recomputed by its audit',
    'none: descriptive':zh?'描述性':'descriptive'})[b];
  const inconclusive={en:'inconclusive at this sample size',zh:'在这个样本量下无法下结论'},notRead={en:'not read: at floor',zh:'处于下限，不读界值'};
  const hasFig=(h,f,x)=>h.includes(`data-fig="${SRF}|${f}|${x}"`);
  const rowOf=(h,attr)=>{const a=h.indexOf(attr);return a<0?null:h.slice(h.lastIndexOf('<tr',a),h.indexOf('</tr>',a));};
  const cellOf=(row,name)=>{const a=row.indexOf(`data-cell="${name}"`);assert.ok(a>0,'a route-2 row without its '+name+' cell');return row.slice(row.lastIndexOf('<td',a),row.indexOf('</td>',a));};
  const words=c=>decodeHtml(c.replace(/<small[\s\S]*?<\/small>/g,'').replace(/<[^>]+>/g,'')).trim();
  const smalls=c=>[...c.matchAll(/<small([^>]*)>([\s\S]*?)<\/small>/g)].map(m=>({attrs:m[1],text:decodeHtml(m[2].replace(/<[^>]+>/g,'')).trim()}));
  const flagOf=c=>decodeHtml((c.match(/data-flag="([^"]*)"/)||[])[1]??'');
  const ppEntries=list=>list.filter(e=>'estimate_pp' in e),logEntries=list=>list.filter(e=>'log_r' in e);
  // A row: its figures, both flags in words, inconclusive and floor exactly where they apply, its gate and who attached it.
  const checkRow=(row,e,zh,where,attached)=>{
    assert.ok(row,where+': a row for '+e.id+' '+e.level+' '+e.question);
    const est=cellOf(row,'estimate'),logr='log_r' in e;
    if(logr) assert.ok(hasFig(est,'num3',e.log_r)&&hasFig(est,'num3',e.interval_95[0])&&hasFig(est,'num3',e.interval_95[1]),where+': '+e.id+' log R and its interval');
    else assert.ok(hasFig(est,'ppr2',e.estimate_pp)&&hasFig(est,'sgr2',e.interval_95_pp[0])&&hasFig(est,'ppr2',e.interval_95_pp[1]),where+': '+e.id+' '+e.question+' difference and its interval');
    const d=cellOf(row,'difference'),m=cellOf(row,'margin'),g=cellOf(row,'gate');
    assert.ok(flagOf(d)===e.difference&&words(d)===diffWords(e,zh),where+': '+e.id+' '+e.question+' says "'+diffWords(e,zh)+'", not "'+words(d)+'"');
    assert.ok(flagOf(m)===e.margin&&words(m)===marginWords(e,zh),where+': '+e.id+' '+e.question+' prints its margin flag with the margin'+(e.margin==='non-inferior'?' and the arm it clears':''));
    const ms=smalls(m).map(x=>x.text);
    assert.equal(ms.includes(inconclusive[zh?'zh':'en']),e.wording==='inconclusive at this sample size',where+': '+e.id+' '+e.question+': "inconclusive" exactly where the export says so');
    assert.equal(ms.includes(notRead[zh?'zh':'en']),e.gate==='floor',where+': '+e.id+' '+e.question+': the margin is not read exactly at floor');
    assert.ok(flagOf(g)===e.gate&&words(g)===gateWords(e.gate,zh),where+': '+e.id+' '+e.question+' gate in words');
    if(attached) assert.ok(smalls(g).some(x=>x.text===byWords(e.gate_attached_by,zh)),where+': '+e.id+' '+e.question+' says who attached its gate');
  };
  // BOAS figures: leaves of the BOAS block that no other block of the export carries.
  const leavesIn=v=>{const out=new Set();const walk=x=>{if(typeof x==='number')out.add(x);else if(x&&typeof x==='object')Object.values(x).forEach(walk);};walk(v);return out;};
  const other=leavesIn([DS.openbmi,DS.eesm19,R.design,R.audits,R.boas_conditions.minimum_cell_people]);
  const boasOnly=new Set([...leavesIn([DS.boas,R.boas_conditions.smallest_cell_people])].filter(v=>!other.has(v)));
  const tokenSet=vals=>{const out=new Set();for(const v of vals)for(const k of ['pct1','ppr2','sgr2','num3','auc3','count','ms2'])for(const n of numbers(fmt[k](v)))out.add(n);return out;};
  const otherTok=tokenSet(other),boasTok=new Set([...tokenSet(boasOnly)].filter(t=>!otherTok.has(t)));
  const noBoasFigure=(text,where)=>{for(const n of numbers(text))assert.ok(!boasTok.has(n),where+': "'+n+'" is a BOAS figure, printed where BOAS\'s three gaps are not');};
  const spanOf=(h,at)=>{const tag=h.slice(at+1).match(/^\w+/)[0],re=new RegExp(`<${tag}\\b|</${tag}>`,'g');re.lastIndex=at;let depth=0,m;
    while((m=re.exec(h))){depth+=m[0].startsWith('</')?-1:1;if(!depth)return [at,m.index];}return [at,h.length];};
  const gapsBlock=(block,zh,where)=>{
    const t=decodeHtml(block.replace(/<[^>]+>/g,' ')).replace(/\s+/g,' ');
    const C=R.boas_conditions;
    for(const g of C.gaps) assert.ok(zh?(t.includes(SRZ[g])&&t.includes(g)):t.includes(g),where+': the BOAS gap "'+g.slice(0,50)+'"'+(zh?' in Chinese with its English':''));
    assert.ok(t.includes(zh?'被试在公开发布中是假名化的。':'Participants are pseudonymised in the public release.')&&t.includes(C.attribution)&&t.includes(zh?SRZ[C.not_an_evaluation_of]:C.not_an_evaluation_of),
      where+': the BOAS block names the participants\' wording, the credit and what is not evaluated');
    assert.ok(t.includes(zh?'所有者决定，2026 年 10 月 7 日':'owner decision, 7 October 2026'),where+': the BOAS block dates the owner\'s approval');
  };
  let boasFigs=0,boasPages=0;
  for(const f of htmlPages){
    const h=readFileSync(new URL(f,DIST),'utf8');
    const regions=[...h.matchAll(/<(\w+)\b[^>]*\sdata-boas="true"[^>]*>/g)].map(m=>spanOf(h,m.index)).map(([a,b])=>({a,b,ok:h.slice(a,b).includes('data-boas-gaps="true"')}));
    let here=0;
    for(const m of h.matchAll(new RegExp(`data-fig="${SRF.replace(/\./g,'\\.')}\\|\\w+\\|([^"]+)"`,'g'))){
      if(!boasOnly.has(Number(m[1])))continue;
      assert.ok(regions.some(r=>r.ok&&r.a<m.index&&m.index<r.b),f+': the BOAS figure '+m[1]+' lies outside every element that carries the three gaps');
      here++;boasFigs++;}
    if(here){boasPages++;
      for(const [,blk] of h.matchAll(/(<div class="protocol-note sr-boas-note" data-boas-gaps="true">[\s\S]*?<\/div>)/g)) gapsBlock(blk,f.startsWith('zh/'),f);}
  }
  assert.ok(boasFigs>300&&boasPages>=8,'BOAS figures read, each beside its gaps ('+boasFigs+' on '+boasPages+' pages)');
  // The topic page, both languages.
  const secOf=(h,id)=>{const a=h.search(new RegExp(`<section\\b[^>]*\\sid="${id}"`));assert.ok(a>0,'section #'+id+' renders');const [s,e]=spanOf(h,a);return h.slice(s,e);};
  const p1=(d,q)=>d.entries.find(e=>e.id==='P1'&&e.level==='E1'&&e.question===q);
  let rows=0;
  for(const [label,pfx] of [['en',''],['zh','zh/']]){
    const zh=label==='zh',path=pfx+'topics/shared-encoder/',html=pageOf(path),where=path;
    const order=['design','motor-imagery','sleep','eesm19','secondary','methods-and-limits'].map(id=>html.search(new RegExp(`<section\\b[^>]*\\sid="${id}"`)));
    assert.ok(order.every((x,i)=>x>0&&(!i||x>order[i-1])),where+': design, motor imagery, sleep, EESM19, secondary, limits, in that order');
    const main=html.slice(html.indexOf('<main'),html.indexOf('<nav class="topic-switcher"'));
    assert.ok([...main.matchAll(/data-fig="([^|"]+)\|/g)].every(m=>m[1]===SRF),where+': every figure is a leaf of the route-2 export');
    // Every figure-like token is a value of the export as the site prints it, or a number in its own text.
    const allTok=new Set();const walkT=v=>{if(typeof v==='number'){for(const g of Object.values(fmt))for(const n of numbers(g(v)))allTok.add(n);}else if(typeof v==='string'){for(const n of numbers(v))allTok.add(n);}else if(v&&typeof v==='object')Object.values(v).forEach(walkT);};walkT(sr);
    const body=main.slice(main.indexOf('<section class="short-answer"'));
    for(const t of [...visible(body).matchAll(/\d+\.\d+|\d{1,3}(?:,\d{3})+/g)].map(m=>m[0])) assert.ok(allTok.has(t),where+': "'+t+'" is not a value of the route-2 export');
    // The short answer and the description: the route verdicts with their margin, and no BOAS figure.
    const ans=visible(html.slice(html.indexOf('<section class="short-answer"'),html.indexOf('</section>',html.indexOf('<section class="short-answer"'))));
    const desc=decodeHtml(html.match(/<meta name="description" content="([^"]*)"/)[1]);
    noBoasFigure(ans,where+' short answer');noBoasFigure(desc,where+' description');
    const a1=p1(DS.openbmi,'MI-A'),aS=p1(DS.boas,'SL-A');
    assert.ok(ans.includes(fmt.ppr2(a1.estimate_pp))&&ans.includes(fmt.sgr2(a1.interval_95_pp[0]))&&ans.includes(fmt.ppr2(a1.interval_95_pp[1]))&&ans.includes(`${DELTA} pp`),where+': the short answer gives the motor-imagery P1 contrast and the margin');
    assert.equal(ans.includes(zh?`整个区间都高于 ${DELTA} pp`:`its whole interval lay above ${DELTA} pp`),aS.interval_95_pp[0]>DELTA,where+': the short answer says the BOAS interval lies above the margin exactly when it does');
    // Review of 2026-10-07: the verdict as tested ("not supported"), not a categorical "not at a lower cost".
    assert.ok(!DS.openbmi.route_sentence.supported&&!DS.boas.route_sentence.supported&&ans.trim().startsWith(zh?'简答 在这些数据上，没能证明更省的设置也一样好。':'Short answer The cheaper set-up was not shown to do as well, on these data.'),where+': the short answer opens with the route verdict as tested');
    // P5 read by its flags: naming the question adds nothing (equivalent on both motor-imagery questions, B-sh
    // non-inferior on sleep). That assigns no gain to the hidden layer: at a 2 pp margin an equivalence cannot account
    // for a 1.48 pp lift, and B-sh − B-lin (S2) is inconclusive on imagery or rest. P2 on which hand with both flags in
    // words; the other counted P2 contrasts, inconclusive, said so.
    const E1=(d,id,q)=>d.entries.find(e=>e.id===id&&e.level==='E1'&&e.question===q);
    const p5m=['MI-A','MI-B'].map(q=>E1(DS.openbmi,'P5',q)),p5s=E1(DS.boas,'P5','SL-A'),p2b=E1(DS.openbmi,'P2','MI-B');
    assert.equal(ans.includes(zh?`在两个运动想象问题上都与那个分类头在 ±${DELTA} pp 内等效`:`equivalent to that head within ±${DELTA} pp on both motor-imagery questions`),p5m.every(e=>e.margin==='equivalent within delta'),where+': the short answer says P5 is equivalent on motor imagery exactly when it is');
    assert.equal(ans.includes(zh?`在睡眠上非劣（界值 ${DELTA} pp）`:`non-inferior at ${DELTA} pp on sleep`),p5s.margin==='non-inferior'&&p5s.interval_95_pp[1]<DELTA,where+': the short answer says the layer not told the question is non-inferior on sleep exactly when it is');
    assert.doesNotMatch(ans,zh?/来自它多出的隐藏层|高出的部分来自/:/came from the head’s extra hidden layer|gain is the hidden layer|whatever lifted/,where+': the short answer assigns no gain to the hidden layer');
    assert.ok(ans.includes(fmt.ppr2(p2b.estimate_pp))&&ans.includes(fmt.sgr2(p2b.interval_95_pp[0]))&&ans.includes(fmt.ppr2(p2b.interval_95_pp[1])),where+': the short answer gives P2 on which hand with its interval');
    assert.equal(ans.includes(zh?`显示出差异，而且不能排除损失达到 ${DELTA} pp 或以上`:`a difference, and a loss of ${DELTA} pp or more cannot be ruled out`),p2b.difference==='difference: A higher'&&p2b.margin==='margin not met',where+': P2 on which hand carries both flags in words');
    assert.equal(ans.includes(zh?'在想象还是静息和睡眠分期上，这项比较无法下结论':'on imagery or rest and on the sleep stage the comparison was inconclusive'),[E1(DS.openbmi,'P2','MI-A'),E1(DS.boas,'P2','SL-A')].every(e=>e.wording==='inconclusive at this sample size'),where+': the other counted P2 contrasts, inconclusive');
    // The route verdicts: the export's route sentences, the counted questions, the floor named.
    for(const [ds,d] of [['openbmi',DS.openbmi],['boas',DS.boas]]){
      const rs=d.route_sentence,a=html.indexOf(`data-route-verdict="${ds}"`),box=html.slice(a,html.indexOf('</div></div>',a));
      assert.ok(a>0&&box.includes(`data-supported="${rs.supported}"`)&&box.includes(rs.supported?'':(zh?'“固定分类头以更少的代价做得一样好”：未得到支持':'Fixed heads did as well for less: not supported')),where+': '+ds+' verdict follows its route sentence');
      for(const q of rs.counted) assert.ok(hasFig(box,'ppr2',p1(d,q).estimate_pp),where+': '+ds+' verdict prints P1 on the counted '+q);
      for(const q of Object.keys(rs.excluded)){const g=d.gates.find(x=>x.level==='E1'&&x.question===q);
        assert.ok(rs.excluded[q]==='floor'&&g.gate==='floor'&&hasFig(box,'pct1',g.mean)&&box.includes(zh?'处于下限':'at floor'),where+': '+ds+' verdict names '+q+' at floor with its fixed-head score');}
      assert.ok(!/C1 is \d|is \d+(?:\.\d+)? pp better|好 \d+(?:\.\d+)? pp/.test(visible(box)),where+': "margin not met" is never read as a size');
    }
    // Every contrast row, both flags in words.
    for(const [ds,list,attached] of [['openbmi',ppEntries(DS.openbmi.entries),false],['boas',ppEntries(DS.boas.entries),false],['boas',E2.entries,true],['eesm19',DS.eesm19.secondary,true]])
      for(const e of list){checkRow(rowOf(html,`data-sr-contrast="${ds}|${e.level}|${e.id}|${e.question}"`),e,zh,where,attached);rows++;}
    assert.equal((html.match(/data-sr-contrast="/g)||[]).length,DS.openbmi.entries.length+ppEntries(DS.boas.entries).length+E2.entries.length+DS.eesm19.secondary.length,where+': one row per contrast, no other');
    for(const e of logEntries([...DS.boas.entries,...DS.boas.secondary])){checkRow(rowOf(html,`data-sr-logr="boas|${e.id}|${e.question}"`),e,zh,where,e.role!=='primary');rows++;}
    // The secondary panel: collapsed; every secondary contrast with its gate and who attached it; S2 on frozen features the audit's.
    const sec=secOf(html,'secondary');
    assert.match(sec,/<details class="rd-panel sr-panel">/,where+': the secondary results sit in a collapsed panel');
    for(const [ds,d] of [['openbmi',DS.openbmi],['boas',DS.boas]]) for(const e of ppEntries(d.secondary)){
      const row=rowOf(sec,`data-sr-secondary="${ds}|${e.level}|${e.id}|${e.question}|${escHtml(e.x)}|${escHtml(e.y)}"`);checkRow(row,e,zh,where+' #secondary',true);rows++;
      assert.equal(/data-computed-by="audit"/.test(row),!!e.computed_by,where+': '+e.id+' '+e.level+' '+e.question+': "computed by the independent audit" exactly where the export says so');}
    // E2 sleep: its disclosure, beside its figures; the stage-only read-out beside SL-E and SL-F; the derivable question.
    const sleep=secOf(html,'sleep'),dis=sleep.slice(sleep.indexOf('data-e2-disclosure="true"'),sleep.indexOf('</p>',sleep.indexOf('data-e2-disclosure="true"')));
    // "None outlived its fit" (review of 2026-10-07): some checkpoints were replaced by their fit's next one, not deleted.
    // Since 2026-10-08 (owner decision) it says when it ran relative to the other results, not on which date.
    for(const s of zh?['这一组运行时，本次运行的其他所有结果','在冻结协议时就已确定','没有任何一项是根据结果选的','临时的私有检查点','没有一个留到拟合结束之后']
                     :['ran after every other result of the run','were fixed when the protocol was frozen','nothing about it was chosen from results','temporary private checkpoints','so none outlived its fit'])
      assert.ok(visible(dis).includes(s),where+': the E2-sleep disclosure says "'+s+'"');
    assert.ok(E2.run_after_other_results&&hasFig(dis,'count',E2.resume_checkpoints.left_after_the_run)&&hasFig(dis,'count',E2.fits),where+': the disclosure counts the fits and the checkpoints left');
    assert.ok(sleep.indexOf('data-e2-disclosure')<sleep.indexOf('data-sr-contrast="boas|E2|'),where+': the disclosure comes before the E2 figures');
    const lede=sleep.slice(0,sleep.indexOf('data-boas-gaps'));
    for(const q of ['SL-E','SL-F']) assert.ok(hasFig(lede,'pct1',DS.boas.secondary.find(e=>e.id==='S11-oracle'&&e.question===q).mean),where+': '+q+' beside the stage-only read-out');
    assert.ok(visible(lede).includes(zh?'SL-E 和 SL-F 在很大程度上可以由当前分期预测':'SL-E and SL-F are largely predictable from the current stage'),where+': the stage sentence');
    assert.ok(sleep.indexOf('data-boas-gaps')<sleep.indexOf('data-route-verdict'),where+': BOAS\'s gaps come before its first result');
    // Where the conditioned head's lift comes from (review of 2026-10-07): B-sh − B-lin (S2, secondary) beside the
    // reading. On motor imagery it is printed and inconclusive, and no gain is assigned to the hidden layer; on the
    // sleep stage the gain is the hidden layer's only while S2 shows B-sh higher, its figure beside the sentence.
    const rd=id=>{const a=html.indexOf(`data-reading="${id}"`);return html.slice(a,html.indexOf('</p>',a));};
    const s2=(d,q)=>d.secondary.find(e=>e.id==='S2'&&e.level==='E1'&&e.question===q),s2a=s2(DS.openbmi,'MI-A'),s2s=s2(DS.boas,'SL-A');
    assert.ok(hasFig(rd('openbmi'),'ppr2',s2a.estimate_pp)&&hasFig(rd('openbmi'),'sgr2',s2a.interval_95_pp[0])&&s2a.wording==='inconclusive at this sample size'
      &&visible(rd('openbmi')).includes(zh?'次要对比 S2），在想象还是静息上为':'(B-sh − B-lin, secondary S2), was ')&&!/来自隐藏层|gain is the hidden layer/.test(visible(rd('openbmi'))),where+': on motor imagery the hidden layer\'s own contrast is printed, inconclusive, and gets no gain');
    assert.equal(visible(rd('boas')).includes(zh?'在睡眠分期上，高出的部分来自隐藏层':'On the sleep stage the gain is the hidden layer’s'),s2s.difference==='difference: B-sh higher'&&s2s.interval_95_pp[0]>0&&hasFig(rd('boas'),'ppr2',s2s.estimate_pp),where+': the gain is the hidden layer\'s only where S2 shows it, its figure beside');
    // The gate's rule is the interval's: the L1 MI-B mean lies above the floor, its interval not wholly (review of 2026-10-07).
    const gm=visible(html.slice(html.indexOf('data-gates="openbmi"'),html.indexOf('</p>',html.indexOf('data-gates="openbmi"')))),fg=DS.openbmi.gates.find(g=>g.level==='L1'&&g.question==='MI-B');
    assert.ok(fg.gate==='floor'&&fg.interval_95[0]<=fg.floor&&gm.includes(zh?`区间没有完全高于 ${fmt.pct1(fg.floor)} 的下限`:`its interval does not lie wholly above the ${fmt.pct1(fg.floor)} floor`)&&!(zh?/没有高于/:/\bnot above\b/).test(gm),where+': the gate sentence states the interval rule, not the mean');
    // "Not supported", never "refuted": an unmet margin is not a refutation (the Chinese said 不成立).
    if(zh) assert.doesNotMatch(visible(main),/不成立/,where+': "not supported" is 未得到支持, not 不成立');
    // EESM19: crude, one seed, the stage sentence, another protocol than the scalp subset.
    const e19=visible(secOf(html,'eesm19'));
    for(const s of zh?['粗略重复','1 个随机种子','在很大程度上可以由当前分期预测','与核心矩阵中类别平衡的头皮子集是不同的协议']:['crude replication','one seed','largely predictable from the current stage','A different protocol from the balanced scalp subset'])
      assert.ok(e19.includes(s),where+': EESM19 says "'+s+'"');
    // The design: the margin, fixed before any result; the multiplicity statement.
    const mult=visible(html.slice(html.indexOf('id="multiplicity"'),html.indexOf('</p>',html.indexOf('id="multiplicity"'))));
    const nPrimary=[...DS.openbmi.entries,...DS.boas.entries].filter(e=>e.role==='primary').length;
    assert.ok(mult.includes(zh?`主分析共有 ${nPrimary} 项比较，不做多重比较校正`:`There are ${nPrimary} primary comparisons and no multiplicity correction`)&&mult.includes(zh?'约每 20 项就可能有 1 项偶然显示出差异':'about one in 20 comparisons with no true difference may show one by chance'),where+': the multiplicity statement');
    assert.ok(visible(secOf(html,'design')).includes(zh?`界值是 ±${DELTA} pp，由所有者在任何结果出来之前定下`:`margin of ±${DELTA} pp, fixed by the owner before any result`),where+': the margin, fixed before any result');
    // Limits: every required limitation and every not-run item, in the page's language; the literature and the credits.
    const lim=secOf(html,'methods-and-limits'),limItems=[...lim.matchAll(/<ul class="rd-rules sr-limits">([\s\S]*?)<\/ul>/g)][0][1];
    assert.deepEqual([...limItems.matchAll(/<li>([\s\S]*?)<\/li>/g)].map(m=>decodeHtml(m[1])),required.map(x=>zh?SRZ[x]:x),where+': every required limitation, in the page\'s language, in the export\'s order');
    const nr=visible(lim.slice(lim.indexOf('sr-not-run'),lim.indexOf('</ul>',lim.indexOf('sr-not-run'))));
    for(const [a,b] of [...R.not_run.map(x=>[x.arm,x.status]),...R.not_reported.map(x=>[x.item,x.status])]) assert.ok(nr.includes(zh?SRZ[a]:a)&&nr.includes(zh?SRZ[b]:b),where+': not run or not reported: '+a.slice(0,40));
    assert.deepEqual([...lim.slice(lim.indexOf('rd-literature')).matchAll(/<li lang="en"><a href="([^"]+)"/g)].map(m=>m[1]),R.literature.map(x=>x.url),where+': the export\'s five literature anchors, in order');
    for(const d of [DS.openbmi,DS.boas,DS.eesm19]){const a=lim.indexOf(escHtml(d.rights.attribution)),art=a<0?'':lim.slice(lim.lastIndexOf('<article',a),lim.indexOf('</article>',a));
      assert.ok(art.includes(`href="${escHtml(d.rights.licenseUrl)}"`)&&art.includes(`href="${escHtml(d.rights.source)}"`),where+': credit, source and licence of '+d.dataset+', in one entry');}
    const au=lim.slice(lim.indexOf('data-audits="true"'),lim.indexOf('</p>',lim.indexOf('data-audits="true"')));
    assert.ok(hasFig(au,'count',R.audits.primary.values_recomputed)&&hasFig(au,'count',R.audits.secondary.values_recomputed)&&hasFig(au,'count',R.audits.e2_sleep.checks),where+': the three audits, counted');
    // No ranking word; the cite block names the route's release alone.
    assert.doesNotMatch(visible(main),/\b(?:best|worst|outperform\w*|beats?|winner)\b|最好|最佳|胜出/i,where+': no ranking word');
    assert.equal(html.slice(html.indexOf('<section class="cite-page"')).match(/data-releases="([^"]+)"/)[1],sr.release_id,where+': the cite block names the route-2 release alone');
  }
  // The cards on the home page and the Questions hub print no BOAS figure.
  for(const page of ['','topics/','zh/','zh/topics/']){const h=pageOf(page),a=h.search(/<a class="topic-entry-card" href="(?:\/zh)?\/topics\/shared-encoder\/"/);
    assert.ok(a>0,(page||'/')+': the route-2 card');noBoasFigure(visible(h.slice(a,h.indexOf('</a>',a))),(page||'/')+' route-2 card');}
  // The dataset and method pages: a route-2 group where its figures are, each row with both flags; the limits note.
  const groupOf=(h,id)=>{const a=h.search(new RegExp(`<section class="entity-group" id="${id}"`));return a<0?null:h.slice(...spanOf(h,a));};
  const noteWords=(e,zh)=>{const low=t=>zh?t:t.replace(/^[A-Z](?=[a-z])/,c=>c.toLowerCase()),sep=zh?'；':'; ';
    return diffWords(e,zh)+sep+low(marginWords(e,zh))+(e.gate==='floor'?(zh?`（${notRead.zh}）`:` (${notRead.en})`):'')+(e.wording==='inconclusive at this sample size'?(zh?'：'+inconclusive.zh:': '+inconclusive.en):'')+sep+low(gateWords(e.gate,zh))+(zh?'。':'.');};
  const groupEntries={openbmi:DS.openbmi.entries.filter(e=>['P1','P5','P2','P4'].includes(e.id)),boas:DS.boas.entries.filter(e=>['P1','P5','P2','P4','P3'].includes(e.id)),eesm19:DS.eesm19.secondary};
  const LIMIT_STARTS={openbmi:["The OpenBMI numbers here use route 2's own"],boas:[],eesm19:['EESM19 full (S13) uses every stored epoch']};
  // The stage sentence on the sleep groups is the page's (review of 2026-10-07): the export's "their results are shown
  // beside a stage-only readout" was false on groups, which show no read-out row, so the BOAS group prints the
  // read-out's two figures in the sentence and never that claim; the EESM19 group says none was computed there.
  const stageClaim=required.find(x=>x.startsWith('SL-E and SL-F are largely predictable from the current stage'));
  const oracleOf=q=>DS.boas.secondary.find(e=>e.id==='S11-oracle'&&e.question===q);
  const nPrimaryAll=[...DS.openbmi.entries,...DS.boas.entries].filter(e=>e.role==='primary').length;
  let groupRows=0;
  for(const [label,pfx] of [['en',''],['zh','zh/']]){const zh=label==='zh';
    for(const [page,gid,ds,only] of [...['openbmi','boas','eesm19'].map(ds=>['datasets/'+ds+'/','g-shared-encoder',ds,null]),
        ...['openbmi','boas','eesm19'].map(ds=>['methods/eegnet/',`g-${ds}-shared-encoder`,ds,'E1']),...['openbmi','boas'].map(ds=>['methods/cbramod/',`g-${ds}-shared-encoder`,ds,'L1'])]){
      const where=pfx+page+'#'+gid,g=groupOf(pageOf(pfx+page),gid);
      assert.ok(g&&g.includes(`href="/${pfx}topics/shared-encoder/`),where+': the route-2 group, read on its question');
      assert.equal(/data-boas="true"/.test(g.slice(0,g.indexOf('>'))),ds==='boas',where+': marked data-boas exactly on BOAS');
      for(const e of groupEntries[ds].filter(e=>!only||e.level===only)){
        const key='log_r' in e?`data-fig="${SRF}|num3|${e.log_r}"`:`data-fig="${SRF}|ppr2|${e.estimate_pp}"`,a=g.indexOf(key);
        assert.ok(a>0,where+': '+e.id+' '+e.level+' '+e.question+' printed');
        const row=g.slice(g.lastIndexOf('<tr',a),g.indexOf('</tr>',a)),note=decodeHtml((row.match(/<small class="row-note">([\s\S]*?)<\/small>/)||[])[1]??'');
        assert.equal(note,noteWords(e,zh),where+': '+e.id+' '+e.level+' '+e.question+' carries both flags, the margin and its gate');groupRows++;}
      const n=g.slice(g.indexOf('data-sr-limits='),g.indexOf('</p>',g.indexOf('data-sr-limits=')));
      assert.ok(n.includes(`href="/${pfx}topics/shared-encoder/#methods-and-limits"`)&&LIMIT_STARTS[ds].every(s=>{const en=required.find(x=>x.startsWith(s));return decodeHtml(n).includes(zh?SRZ[en]:en);})
        &&decodeHtml(n).includes(zh?`整个区间落在 ±${DELTA} pp 以内`:`within ±${DELTA} pp, the margin fixed before any result`),where+': what these figures cannot say, the margin and a link to every limitation');
      const nt=decodeHtml(n);
      if(ds==='boas') assert.ok(nt.includes(zh?'SL-E 和 SL-F 在很大程度上可以由当前分期预测：只用真实的当前分期读出，平衡准确率就能达到 ':'SL-E and SL-F are largely predictable from the current stage: read off the true current stage alone, they reach ')
        &&['SL-E','SL-F'].every(q=>hasFig(n,'pct1',oracleOf(q).mean))&&hasFig(n,'count',oracleOf('SL-E').included_people)&&!nt.includes(zh?SRZ[stageClaim]:stageClaim),where+': SL-E and SL-F beside the stage-only read-out\'s figures, never a read-out the group does not show');
      if(ds==='eesm19') assert.ok(nt.includes(zh?'SL-E 和 SL-F 在很大程度上可以由当前分期预测；EESM19 上没有计算只用分期的读出。':'SL-E and SL-F are largely predictable from the current stage; no stage-only read-out was computed on EESM19.'),where+': the stage sentence, and that no read-out was computed');
      // The multiplicity statement travels with the results (the export's audits, D-5): the count and one in 20.
      assert.ok(nt.includes(zh?`第二条路线有 ${nPrimaryAll} 项主分析比较，另有各项次要比较，在没有真实差异的比较里，约每 20 项就可能有 1 项偶然显示出差异`:`across route 2’s ${nPrimaryAll} primary comparisons and its secondary ones, about one in 20 comparisons with no true difference may show one by chance`),where+': the multiplicity statement travels with the group');
    }
    // No other method page carries a route-2 group.
    for(const f of htmlPages.filter(f=>new RegExp(`^${pfx}methods/[^/]+/index\\.html$`).test(f)&&!/\/(?:eegnet|cbramod)\//.test(f)))
      assert.ok(!readFileSync(new URL(f,DIST),'utf8').includes('-shared-encoder"'),f+': no route-2 group');
    // BOAS's register entry: the ethics committee and reference, written consent, the approval, "pseudonymised"; the index points at its gaps.
    const bp=pageOf(pfx+'datasets/boas/'),rn=bp.slice(bp.indexOf('data-rights-note="boas"'),bp.indexOf('</article>',bp.indexOf('data-rights-note="boas"')));
    const pr=DS.boas.rights.privacyReview,eth=pr.match(/The dataset description states approval by [^.]*\(C\.I\. PI24\/046\)\./)[0],con=pr.match(/The README states that participants[^.]*written informed consent\./)[0];
    assert.ok(decodeHtml(rn).includes(eth)&&decodeHtml(rn).includes(con)&&(!zh||(decodeHtml(rn).includes(SRZ[eth])&&decodeHtml(rn).includes(SRZ[con]))),pfx+'datasets/boas/: the ethics committee, its reference and written consent'+(zh?', in Chinese with the English':''));
    assert.ok(visible(rn).includes(zh?'被试在公开发布中是假名化的。':'Participants are pseudonymised in the public release.')&&rn.includes(R.boas_conditions.owner_approval.approved_on),pfx+'datasets/boas/: the approval and the participants\' wording');
    assert.ok(bp.includes(`href="${DS.boas.rights.licenseUrl}"`)&&bp.includes(DS.boas.rights.license)&&bp.includes('class="entity-profile"'),pfx+'datasets/boas/: CC0 linked, and the sourced profile');
    const ix=pageOf(pfx+'datasets/');assert.ok(ix.includes(`href="/${pfx}datasets/boas/"`)&&/data-boas-pointer="true"/.test(ix),pfx+'datasets/: the BOAS row and the pointer to its gaps');
    // The release log names the new question; when-not-to-act prints no route-2 figure and does not cite the release.
    const rel=pageOf(pfx+'releases/'),ra=rel.indexOf(`id="${sr.release_id}"`),entry=rel.slice(ra,rel.indexOf('</article>',ra));
    assert.ok(entry.includes(`href="/${pfx}topics/shared-encoder/"`),pfx+'releases/: the route-2 release names its question');
    // Review of 2026-10-07: what is withheld is the measured compute totals, as the export's not_published says; the
    // page's cost ledger prints the indicative step times. The hidden layer carries the lift on sleep only; no
    // checkpoint outlived its fit.
    const ev=visible(entry),du=zh?null:visible(pageOf('data-use/').slice(pageOf('data-use/').indexOf('id="sources-2026-10-07"')));
    for(const [t,w] of [[ev,pfx+'releases/'],...(du?[[du.slice(0,du.indexOf('Release ')),'data-use/#sources-2026-10-07']]:[])])
      assert.ok(t.includes(zh?'实测的计算总量（GPU 小时、每次拟合与每组的实际耗时、每个外层折的训练步数）':'measured compute totals (GPU-hours, wall time per fit and per block, training steps per outer fold)')
        &&t.includes(zh?'“仅供参考”的标注发布在共享 GPU 上交替测得的两项耗时':'labelled indicative, the two times measured interleaved on a shared GPU')&&!/measured compute time;|实测的计算耗时；/.test(t),w+': the compute items withheld, and the indicative times the ledger prints');
    assert.ok(ev.includes(zh?'在运动想象上，这个隐藏层与固定头的对比无法下结论':'on motor imagery its own contrast with the fixed heads was inconclusive')&&!/whatever lifted|同一个隐藏层不加条件时也有/.test(ev)
      &&ev.includes(zh?'没有一个留到对应的拟合结束之后':'none outlived its fit'),pfx+'releases/: the lift is the hidden layer\'s on sleep only, and no checkpoint outlived its fit');
    const w=pageOf(pfx+'topics/when-not-to-act/');
    assert.ok(!w.includes(`data-fig="${SRF}|`)&&!w.slice(w.indexOf('<section class="cite-page"')).includes(sr.release_id),pfx+'topics/when-not-to-act/: links route 2, prints none of its figures and does not cite it');
  }
  const nRows=DS.openbmi.entries.length+ppEntries(DS.boas.entries).length+E2.entries.length+DS.eesm19.secondary.length+logEntries([...DS.boas.entries,...DS.boas.secondary]).length
    +ppEntries(DS.openbmi.secondary).length+ppEntries(DS.boas.secondary).length;
  assert.ok(rows===2*nRows&&groupRows>=100,'route-2 rows read ('+rows+' on the topic, '+groupRows+' in groups)');
}
console.log('PASS: 2026-10-07 route 2 on the site — /topics/shared-encoder/: every contrast with both flags in words, the margin with them, inconclusive and floor exactly where the export says, gates with who attached them; route verdicts from the route sentences; BOAS figures always inside an element holding the three gaps, the credit and "pseudonymised" (none in the short answer, description or cards); E2 sleep disclosed before its figures; EESM19 crude with the stage sentence; SL-E and SL-F beside the stage-only read-out; secondary results collapsed; limits in the page\'s language with exactly the English\'s numbers; route-2 groups on the OpenBMI, BOAS, EESM19, EEGNet and CBraMod pages with both flags; BOAS register entry; release log; when-not-to-act links without citing.');
// --- 2026-10-04 v9 foundation models: the pages ----------------------------------------------------
// The v9 rows on the site (owner approval 2026-10-04): a section of their own on every protocol page
// (#foundation-v9) and a group under the released rows in the home page's per-protocol table, the
// masking-ablation siblings in a panel of their own, the EEGMAT adaptation on arithmetic-rest, a
// group per protocol on each core dataset page, a method page per model family, the model
// directory's cards, and the owner's sourced exposure statement for LaBraM and CBraMod beside the
// released sentence. Every figure is re-read from the served CSV or JSON (the generic data-fig loop
// above); what is pinned here is that each row is its CSV row, column by column and in order; a cell
// not run carries its reason and no figure; the chance flags follow the core rule and the CSV's own
// flag; the exposure badge, statement and source are the exposure table's, ZUNA 1.1 unknown on every
// cell; the row footnote, the licence note and ZUNA 1.1's research-use sentence travel with the rows;
// nothing is ranked; the Chinese is the translation table's, with the English beside it.
{
  const REL='foundation-models-update-20261004', FMJ='foundation-models-update.json';
  const F=JSON.parse(readFileSync(new URL('data/'+FMJ,DIST),'utf8')).results['foundation-models-v9'];
  const E=F.pretraining_exposure;
  const e=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const textOf=s=>decodeHtml(s.replace(/<[^>]+>/g,' ')).replace(/\s+/g,' ').trim();
  // The translation table, evaluated from its source (type-only import and `export` removed).
  const zhSrc=stripTypeScriptTypes(readFileSync(new URL('../src/data/foundation-models-zh.ts',import.meta.url),'utf8'))
    .replace(/^import[^\n]*\n/gm,'').replace(/^export /gm,'');
  const zhCtx={};vm.runInNewContext(zhSrc+'\nthis.fmZh=fmZh;',zhCtx);const Z=zhCtx.fmZh;
  // Every key is a sentence of the export, every translation carries exactly its English's numbers
  // and is Chinese, no rejected rendering, and no key outlives its text.
  {
    const strings=new Set();const walk=v=>{if(typeof v==='string')strings.add(v);else if(v&&typeof v==='object')Object.values(v).forEach(walk);};walk(F);
    // A version label ("v9") is not a figure: the Chinese may drop it (no version labels on the site, 2026-10-08).
    const digits=s=>[...s.replace(/(?<![\w.])v\d+(?![\w.])/g,' ').matchAll(/\d[\d,]*(?:\.\d+)?/g)].map(m=>m[0]).sort();
    for(const [en,zh] of Object.entries(Z)){
      assert.ok(strings.has(en),'foundation-models-zh.ts: "'+en.slice(0,50)+'" matches no text in the v9 export');
      assert.deepEqual(digits(zh),digits(en),'foundation-models-zh.ts: the Chinese for "'+en.slice(0,50)+'" must carry exactly its numbers');
      if(!/^(?:MIT|Apache-2\.0)\.?$/.test(en)) assert.ok(/\p{Script=Han}/u.test(zh),'foundation-models-zh.ts: "'+en.slice(0,50)+'" has no Chinese');
      for(const [bad,good] of Object.entries(rejected)) assert.ok(!hasRejected(zh,bad),`foundation-models-zh.ts: "${bad}" is a rejected rendering — use "${good}"`);
    }
    // The REVE sensitivity runs keep their direction in Chinese (review of 2026-10-05): the numbers alone cannot tell
    // 高 from 低.
    for(const [k,dir] of [['reve-base','P300 的得分高 0.71、睡眠低 1.40'],['reve-large','P300 的得分低 2.06、睡眠低 0.93']])
      assert.ok((Z[F.models.find(m=>m.id===k).row_footnote]||'').includes(dir),'foundation-models-zh.ts: '+k+'\'s footnote says "'+dir+'"');
  }
  const say=(en,label)=>{const shown=EN_SHOWN[en]??en;return label==='en'?{text:shown}:{text:Z[en],original:Z[en]===en||/^(?:MIT|Apache-2\.0)\.?$/.test(en)?undefined:shown};};
  const printed=(html,en,label)=>{const t=say(en,label);assert.ok(t.text,'no Chinese for "'+en.slice(0,50)+'"');
    return html.includes(e(t.text))&&(!t.original||html.includes('<span class="note-original" lang="en">'+e(t.original)+'</span>'));};
  // Independent of foundation-models.ts: each checkpoint's page and exposure-table key.
  const SLUG={'reve-base':'reve','reve-large':'reve','luna-base':'luna','luna-large':'luna','brainomni-base':'brainomni',codebrain:'codebrain',eegmamba:'eegmamba',
    'steegformer-base':'st-eegformer','steegformer-large':'st-eegformer','eeg-fm-masking/mae-r9cm-L2':'eeg-fm-masking','eeg-fm-masking/jepa-r9cm-L2':'eeg-fm-masking',
    'eeg-fm-masking/mae-rone-L1':'eeg-fm-masking','eeg-fm-masking/jepa-rone-L1':'eeg-fm-masking','erp-fm-base':'erp-fm',singlem:'singlem',zuna:'zuna'};
  const XKEY={...SLUG,'reve-base':'reve-base','reve-large':'reve-large','brainomni-base':'brainomni','steegformer-base':'st-eegformer','steegformer-large':'st-eegformer','erp-fm-base':'erp-fm',zuna:'zuna-1.1'};
  assert.deepEqual(Object.keys(SLUG).sort(),F.models.map(m=>m.id).sort(),'every checkpoint has a method page');
  const slugs=[...new Set(Object.values(SLUG))];
  const dsKeyOf=p=>E.datasets.find(d=>d.protocols.includes(p)).key;
  const xcell=(key,p)=>E.cells.find(c=>c.model===key&&c.dataset===dsKeyOf(p));
  const statementIn=(st,label)=>label==='en'?st:Z[st];
  const MVPSLUG={ds003810:'ds003810',EEGMAT:'eegmat','EESM19 scalp subset':'eesm19',BETA:'beta','TMNRED / ds005383':'tmnred',ds006593:'ds006593',ds005342:'ds005342'};
  const research={en:'Model card: research use only, not for diagnosis or clinical use.',zh:'模型卡：仅供研究使用，不可用于诊断或临床。'};
  const csvOf=p=>{const [h,...b]=csvRows(readFileSync(new URL('data/foundation-models-'+p+'.csv',DIST),'utf8')).filter(r=>r.length>1);return b.map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i]])));};
  const matrix=F.models.filter(m=>m.panel==='matrix'),ablation=F.models.filter(m=>m.panel!=='matrix');
  const ranking={en:/\b(?:best|top|winner|leader|outperform\w*|beats?)\b|\branked\b(?<!never ranked)(?<!not ranked)/i,zh:/最佳|最好的|胜出|排名第/};
  const notProof={en:/\bnot exposed\b|\bproven\b|\bno overlap\b/i,zh:/已证明|证明没有|没有重叠/};
  const bodyRows=grp=>{const tb=grp.indexOf('<tbody>');return tb<0?0:(grp.slice(tb,grp.indexOf('</tbody>',tb)).match(/<tr>/g)||[]).length;};
  const NAME={reve:'REVE',luna:'LUNA',brainomni:'BrainOmni',codebrain:'CodeBrain',eegmamba:'EEGMamba','st-eegformer':'ST-EEGFormer','eeg-fm-masking':'eeg-fm-masking',
    'erp-fm':'ERP-FM',singlem:'SingLEM',zuna:'ZUNA',labram:'LaBraM',cbramod:'CBraMod'};
  // Licence notes travel with the rows (review of 2026-10-05). REVE's licence asks for the model version to be named:
  // each REVE checkpoint's revision from the export, wherever its licence entry is printed.
  const reveVersions=F.models.filter(m=>SLUG[m.id]==='reve').map(m=>`${m.name} @ ${m.revision.split(' @ ').at(-1)}`).join(' · ');
  assert.ok(/REVE Base @ [0-9a-f]{8} · REVE Large @ [0-9a-f]{8}/.test(reveVersions)&&/name the model version/.test(F.models.find(m=>m.id==='reve-base').licence_note),'REVE: its licence asks for the version, and the export names both');
  const endorse={en:'No model’s authors endorse these results',zh:'任何模型的作者都没有为这些结果背书'};
  const licName=m=>m.weights_licence.replace(/\s*[(;].*$/,'');
  // A v9 group's weights terms: each licence of the checkpoints in its rows, REVE's versions where REVE is there,
  // no endorsement, and a link to the protocol page's full list, which must exist.
  const termsOk=(grp,label,prefix,where)=>{
    const m=grp.match(/<p class="protocol-note fm-terms-note" data-fm-terms="([^"]+)">([\s\S]*?)<\/p>/);
    assert.ok(m,where+': the group prints the weights terms of its rows');
    const ms=F.models.filter(x=>grp.includes(`>${e(x.name)}</a>`));
    assert.ok(ms.length,where+': the group has v9 rows');
    for(const x of ms) assert.ok(m[2].includes(label==='zh'&&/^REVE /.test(licName(x))?'REVE 负责任使用许可 v1.0':licName(x)),where+': the terms name '+x.name+'\'s licence ('+licName(x)+')');
    if(ms.some(x=>SLUG[x.id]==='reve')) assert.ok(m[2].includes(ms.filter(x=>SLUG[x.id]==='reve').map(x=>`${x.name} @ ${x.revision.split(' @ ').at(-1)}`).join(' · ')),where+': REVE named by version');
    assert.ok(m[2].includes(endorse[label])&&m[2].includes(`href="/${prefix}protocols/${m[1]}/#v9-licences"`)&&pageOf(prefix+'protocols/'+m[1]+'/').includes('id="v9-licences"'),where+': no endorsement, and the full list linked');
  };
  // ZUNA 1.1's research-use sentence on every one of its rows in a group, and on no other row.
  const zunaRowsOk=(grp,label,where,adapt)=>{
    const trs=[...grp.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(m=>m[1]),z=trs.filter(t=>t.includes('>ZUNA 1.1</a>'));
    assert.ok(z.length>0,where+': ZUNA 1.1 has rows');
    assert.ok(z.every(t=>t.includes(research[label])),where+': ZUNA 1.1\'s research-use sentence on every one of its rows');
    assert.equal(trs.filter(t=>t.includes(research[label])).length,z.length,where+': the research-use sentence belongs to ZUNA 1.1\'s rows');
    if(adapt) assert.ok(z.every(t=>t.includes(label==='en'?'Pretraining exposure: '+e(E.statements.unknown):'是否出现在预训练数据中：'+e(Z[E.statements.unknown]))),where+': ZUNA 1.1\'s adapted rows say its exposure is unknown');
  };

  // 1. Protocol pages.
  for(const t of data.tracks){
    const rows=csvOf(t.id),fmcsv='foundation-models-'+t.id+'.csv',tradeoff=t.type==='tradeoff';
    for(const [label,prefix] of [['en',''],['zh','zh/']]){
      const where=prefix+'protocols/'+t.id+'/',html=pageOf(where);
      const a=html.indexOf('<section class="topic-section fm-section" id="foundation-v9"'),sec=html.slice(a,html.indexOf('</section>',a));
      assert.ok(a>html.indexOf('id="results"')&&a<html.indexOf('id="methods-and-limits"'),where+': the v9 section follows the released results, before the limits');
      assert.ok(sec.includes(`data-release="${REL}"`),where+': the v9 section names its release');
      const main=sec.slice(sec.indexOf('<table class="fm-results">'),sec.indexOf('</table>',sec.indexOf('<table class="fm-results">')));
      const abl=sec.slice(sec.indexOf('id="masking-ablation"'),sec.indexOf('</details>'));
      assert.ok(/<details class="rd-panel fm-ablation" id="masking-ablation">/.test(sec)&&!/id="masking-ablation" open/.test(sec),where+': the masking ablation is its own collapsed panel');
      const tags=part=>[...part.matchAll(/<tr data-fm-row="([^"]+)" data-panel="([^"]+)" data-status="([^"]+)" data-exposure="([^"]+)">/g)];
      assert.deepEqual(tags(main).map(m=>m[1]),matrix.map(m=>m.id),where+': one row per matrix checkpoint, in the export\'s family order, never re-sorted');
      assert.deepEqual(tags(abl).map(m=>m[1]),[F.masking_ablation.checkpoints[0],...ablation.map(m=>m.id)],where+': the ablation panel is the paper-recommended row, then its three siblings');
      assert.ok(tags(main).every(m=>m[2]==='matrix')&&tags(abl).slice(1).every(m=>m[2]==='masking ablation'),where+': panels as the export assigns them');
      const plotRows=(sec.match(/<div class="ip-row">/g)||[]).length;
      if(!tradeoff) assert.equal(plotRows,t.rows.filter(r=>r.interval).length+rows.filter(r=>r.panel==='matrix'&&r.status==='complete').length,where+': the plot shows the released rows and every scored v9 matrix row');
      for(const [part,list] of [[main,tags(main)],[abl,tags(abl)]]) for(const [tag,id,,status,xs] of list){
        const at=part.indexOf(tag),row=part.slice(at,part.indexOf('</tr>',at)),rec=rows.find(r=>r.model_id===id),m=F.models.find(x=>x.id===id);
        const cell=F.frozen_probe.find(c=>c.model===id&&c.protocol===t.id),xc=xcell(XKEY[id],t.id),w=where+'/'+id;
        assert.equal(status,rec.status==='complete'?'complete':'not_run',w+': status (the CSV writes "not run")');
        assert.equal(xs,cell.exposure.status,w+': exposure status');
        assert.equal(xc.statement,rec.pretraining_exposure,w+': the CSV states the exposure table\'s statement');
        assert.ok(row.includes(`href="/${prefix}methods/${SLUG[id]}/"`)&&row.includes('>'+e(m.name)+'<'),w+': name, linked to its method page');
        assert.ok(row.includes('>'+e(rec.evaluation_mode)+'<'),w+': training mode as the CSV states it');
        const figs=[...row.matchAll(/data-fig="([^|"]+)\|\w+\|([^"]+)"/g)];
        assert.ok(figs.every(f=>f[1]===fmcsv),w+': every figure from the protocol\'s v9 CSV');
        const n=k=>Number(rec[k]);
        const expected=rec.status!=='complete'?[n('channels')]
          :tradeoff?[n('primary_percent'),n('commands_detected'),n('command_trials'),n('always_abstain_participants'),n('participants'),n('secondary_value'),
                     n('idle_false_activations'),n('idle_trials'),n('window_balanced_accuracy'),n('window_auroc'),n('channels'),n('participants')]
          :[n('primary_percent'),n('descriptive_interval_low_percent'),n('descriptive_interval_high_percent'),n('secondary_value'),n('channels'),n('participants')];
        assert.deepEqual(figs.map(f=>Number(f[2])),expected,w+': the row must equal its CSV row, column by column');
        if(rec.status!=='complete'){
          assert.match(row,label==='en'?/<strong>Not run<\/strong>/:/<strong>未运行<\/strong>/,w+': a cell not run says so');
          assert.ok(printed(row,rec.not_run_reason,label),w+': with its reason');
          assert.ok(rec.primary_percent===''&&!/\b0\.0%/.test(textOf(row)),w+': never a zero');
        } else if(!tradeoff){
          const c=t.chanceLevel,y=n('primary_percent'),lo=n('descriptive_interval_low_percent'),hi=n('descriptive_interval_high_percent');
          const below=y<=c,reaches=!below&&lo<=c;
          assert.equal(rec.at_or_below_chance,String(below),w+': the CSV\'s at-or-below flag is the core rule');
          assert.equal(rec.interval_includes_chance,String(lo<=c&&c<=hi),w+': the CSV\'s interval flag');
          const fb=label==='en'?/At or below chance level/:/不高于随机水平/,fr=label==='en'?/Interval reaches chance level/:/区间触及随机水平/;
          if(below) assert.match(row,fb,w+': at-or-below-chance must be flagged');
          else if(reaches) assert.match(row,fr,w+': chance-touching interval must be flagged');
          else {assert.doesNotMatch(row,fb,w+': flagged without cause');assert.doesNotMatch(row,fr,w+': flagged without cause');}
        } else if(n('always_abstain_participants')>0) assert.match(row,/class="flag"><span data-fig/,w+': people who always abstained are flagged');
        // Exposure: the table's statement, its badge where it is in the list or unknown, its source.
        const st=e(statementIn(xc.statement,label));
        if(xs==='exposed') assert.ok(row.includes('<span class="flag fm-badge" data-exposure="exposed">'+st+'</span>'),w+': the exposure badge');
        else if(xs==='unknown') assert.ok(row.includes('<span class="flag fm-badge" data-exposure="unknown">'+(label==='en'?'Exposure unknown':'是否出现在预训练数据中：未知')+'</span>')&&row.includes(st),w+': exposure unknown, with the statement');
        else assert.ok(row.includes('<small>'+st+'</small>')&&!row.includes('fm-badge'),w+': the sourced statement, no badge');
        const td=row.slice(row.indexOf('<td class="fm-exposure">'));
        const hrefs=[...td.matchAll(/href="([^"]+)"/g)].map(x=>x[1]);
        assert.ok(hrefs.length&&hrefs.every(h=>xc.urls.includes(decodeHtml(h))),w+': the exposure links its source');
        if(id==='zuna'){assert.equal(xs,'unknown',w+': every ZUNA 1.1 cell is unknown');assert.ok(row.includes(research[label]),w+': the research-use sentence travels with its row');}
        else assert.ok(!row.includes(research[label]),w+': the research-use sentence belongs to ZUNA 1.1');
        // The row's footnote mark leads to its footnote: the export's text.
        const fn=row.match(/<sup class="fn-ref"><a href="#(fn-v9-\d+)">(\d+)<\/a><\/sup>/);
        assert.ok(fn,w+': the row carries its footnote mark');
        const li=sec.slice(sec.indexOf(`<li id="${fn[1]}">`),sec.indexOf('</li>',sec.indexOf(`<li id="${fn[1]}">`)));
        assert.ok(li.length>0&&printed(li,m.row_footnote,label),w+': the footnote is the export\'s row footnote');
      }
      // Weights licences and terms, one entry per family; a note that only restates the name is not repeated.
      const lic=sec.slice(sec.indexOf('<ul class="entity-links protocol-prose fm-licences">'),sec.indexOf('</ul>',sec.indexOf('fm-licences')));
      for(const s of slugs){
        const first=F.models.find(m=>SLUG[m.id]===s),li=lic.slice(lic.indexOf(`<li data-licence="${s}">`),lic.indexOf('</li>',lic.indexOf(`<li data-licence="${s}">`)));
        assert.ok(li.length>0&&printed(li,first.weights_licence,label),where+': the '+s+' weights licence');
        if(first.licence_note.replace(/\.$/,'')!==first.weights_licence) assert.ok(printed(li,first.licence_note,label),where+': the '+s+' licence note');
        assert.ok(li.includes(`href="${first.paper}"`),where+': the '+s+' paper is cited');
      }
      {const rl=lic.slice(lic.indexOf('<li data-licence="reve">'),lic.indexOf('</li>',lic.indexOf('<li data-licence="reve">')));
       assert.ok(rl.includes(reveVersions),where+': the REVE licence entry names the model versions');
       assert.ok(sec.includes('<p class="protocol-note fm-no-endorsement">'+endorse[label]),where+': no author endorses these results, under the licences');}
      // The released limitation keeps its words; where it calls pretraining overlap unknown, a dated pointer follows it.
      {const lim=html.indexOf('<p class="protocol-limitation"'),ptr=html.indexOf('<p class="protocol-note fm-limitation-pointer">');
       if(/pretraining overlap unknown/.test(t.limitation)) assert.ok(ptr>lim&&ptr<html.indexOf('id="steps"')&&html.slice(ptr,html.indexOf('</p>',ptr)).includes('href="#pretraining-exposure"')&&html.slice(ptr,html.indexOf('</p>',ptr)).includes('2026-10-04'),where+': a dated pointer beside "pretraining overlap unknown"');
       else assert.equal(ptr,-1,where+': a pointer without the released words it points from');}
      assert.ok(sec.includes(label==='en'?'which is not proof that its recordings were never seen':'这并不证明它的记录从未被模型见过'),where+': the exposure key says what a statement is not');
      // The notes on the v9 rows: the CSV's, which join the export's sentences; on the Chinese page each sentence in
      // Chinese from the translation table, the English beside it (review of 2026-10-05).
      {const nu=sec.slice(sec.indexOf('<ul class="entity-links protocol-prose fm-notes">'),sec.indexOf('</ul>',sec.indexOf('<ul class="entity-links protocol-prose fm-notes">')));
       for(const rec of rows.filter(r=>r.notes)){
         const m=F.models.find(x=>x.id===rec.model_id),c=F.frozen_probe.find(x=>x.model===m.id&&x.protocol===t.id),parts=[...m.notes,...(c.notes??[])];
         assert.equal(parts.join(' '),rec.notes,where+'/'+m.id+': the CSV\'s notes are the export\'s sentences');
         if(label==='en') assert.ok(nu.includes(e(rec.notes)),where+'/'+m.id+': the notes as the CSV states them');
         else for(const x of parts) assert.ok(printed(nu,x,label),where+'/'+m.id+': the note "'+x.slice(0,40)+'" in Chinese, with the English beside it');
       }}
      // The reading rule fits the rows: interval overlap where there are intervals; the idle rows are counts (review of 2026-10-05).
      assert.equal(/95% intervals do not overlap|95% 区间不重叠/.test(visible(sec.slice(0,sec.indexOf('<table class="fm-results">')))),!tradeoff,where+': the interval reading rule only where rows have intervals');
      if(tradeoff) assert.ok(visible(sec).includes(label==='en'?'they are counts with no interval, so no row is called above or below another':'这些是计数，没有区间，所以不说哪一行高于或低于另一行'),where+': the idle rows are counts, not ranked');
      // Follow-up review of 2026-10-05: the v9 limitations the topics carry, here too — no multiplicity correction where
      // there are intervals (126 frozen cells), windows shorter than the pretraining contexts everywhere — and EEGMamba's
      // exposure read from its official code, with medium confidence, in the exposure key.
      {const lede=visible(sec.slice(0,sec.indexOf('<table class="fm-results">')));
       assert.equal(lede.includes(label==='en'?'Each interval is a descriptive participant bootstrap with no multiplicity correction, and with 126 frozen cells an occasional non-overlap is expected by chance':'每个区间都是描述性的被试 bootstrap，没有做多重比较校正；冻结单元格共有 126 个，偶尔出现不重叠，本身就在随机误差的预料之中'),!tradeoff,where+': no multiplicity correction, where the rows have intervals');
       assert.equal(F.frozen_probe.filter(c=>c.status==='complete').length,126,'v9: 126 frozen cells');
       assert.ok(lede.includes(label==='en'?'Every encoder sees this protocol’s published windows, usually shorter than its pretraining context':'每个编码器看到的都是本协议已发布的时间窗，通常比它预训练时的上下文更短'),where+': the windows are shorter than the pretraining contexts');
       const key=visible(sec.slice(sec.indexOf('<p class="citation-note fm-exposure-key">'),sec.indexOf('</p>',sec.indexOf('<p class="citation-note fm-exposure-key">'))));
       assert.ok(key.includes(label==='en'?'EEGMamba’s list is read from its official code (its paper was not read), with medium confidence':'EEGMamba 的清单读自其官方代码（论文全文没有读过），把握程度为中等'),where+': EEGMamba\'s exposure, read from its code, medium confidence');}
      assert.ok(sec.includes(`href="/data/${fmcsv}" download`)&&sec.includes(`href="/${prefix}releases/#${REL}"`),where+': the v9 CSV and its release are linked');
      const vis=visible(label==='zh'?chineseOnly(sec):sec);
      assert.doesNotMatch(vis,ranking[label],where+': the v9 rows are not ranked');
      assert.doesNotMatch(vis,notProof[label],where+': no exposure claim beyond the authors\' lists');
      // LaBraM and CBraMod beside the released sentence: the sourced statement, its date and sources.
      const ce=html.slice(html.indexOf('<p class="roadmap-p fm-core-exposure">'),html.indexOf('</p>',html.indexOf('<p class="roadmap-p fm-core-exposure">')));
      assert.ok(ce.length>0&&html.indexOf(e(t.pretrainingOverlap))<html.indexOf('fm-core-exposure'),where+': the dated exposure note follows the released sentence, which stays');
      for(const k of ['labram','cbramod']){
        const c=xcell(k,t.id);
        assert.equal(c.status,'not_exposed',where+': '+k+' is absent from its authors\' list');
        for(const u of c.urls) assert.ok(ce.includes(`href="${u}"`),where+': '+k+' source '+u);
      }
      assert.equal(ce.split(e(statementIn(E.statements.not_exposed,label))).length-1,2,where+': the statement, once for each model');
      assert.ok(ce.includes(label==='en'?'Checked 2026-10-04.':'2026-10-04 核查。'),where+': the check date');
      // The EEGMAT adaptation, on arithmetic-rest only.
      const ad=html.indexOf('<table class="fm-adaptation">');
      if(t.id!=='arithmetic-rest'){assert.equal(ad,-1,where+': the adaptation belongs to arithmetic-rest');continue;}
      const body=html.slice(ad,html.indexOf('</table>',ad));
      const A=F.eegmat_adaptation,ctx=A.published_context;
      const arm=x=>[x.balanced_accuracy,...x.interval_95];
      const adRows=[{name:ctx.model,f:[...arm(ctx.arms.frozen),...arm(ctx.arms['lora-r4']),ctx.paired_lora_minus_frozen.mean_change,...ctx.paired_lora_minus_frozen.interval_95,
                     ctx.paired_lora_minus_frozen.helped,ctx.paired_lora_minus_frozen.harmed,ctx.paired_lora_minus_frozen.tied,ctx.arms.frozen.trainable_parameters,ctx.arms['lora-r4'].trainable_parameters],
                     zero:ctx.paired_lora_minus_frozen.interval_95[0]>0||ctx.paired_lora_minus_frozen.interval_95[1]<0},
        ...A.rows.map(r=>{const p=r.paired_lora_minus_frozen;return {name:F.models.find(m=>m.id===r.model).name,id:r.model,
          f:[...arm(r.arms['frozen-ce']),...arm(r.arms['lora-r4']),p.mean_change,...p.interval_95,p.helped,p.harmed,p.tied,r.arms['frozen-ce'].trainable_parameters,r.arms['lora-r4'].trainable_parameters],zero:p.excludes_zero};})];
      assert.deepEqual([...body.matchAll(/<tr data-adapt-row="([^"]+)">/g)].map(m=>decodeHtml(m[1])),adRows.map(r=>r.name),where+': LaBraM for context, then the nine adapted encoders in the export\'s order');
      for(const r of adRows){
        const at=body.indexOf(`<tr data-adapt-row="${e(r.name)}">`),row=body.slice(at,body.indexOf('</tr>',at));
        const figs=[...row.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"/g)];
        assert.ok(figs.every(f=>f[1]===FMJ),where+'/'+r.name+': adaptation figures from the v9 JSON');
        assert.deepEqual(figs.map(f=>Number(f[3])),r.f,where+'/'+r.name+': the adaptation row, arm by arm');
        assert.ok(row.includes(`data-resolved="${r.zero}"`)&&row.includes(label==='en'?(r.zero?'The interval excludes zero.':'The interval includes zero: no change is established.'):(r.zero?'区间不含零。':'区间包含零：不能认定有变化。')),where+'/'+r.name+': the verdict its interval supports');
        if(r.id==='zuna') assert.ok(row.includes('data-exposure="unknown"')&&row.includes(research[label]),where+': ZUNA 1.1 adapted, exposure unknown, research use only');
      }
      const notAdapted=html.slice(html.indexOf('<p class="protocol-note">',ad),html.indexOf('</p>',html.indexOf('<p class="protocol-note">',ad)));
      for(const m of F.models.filter(m=>m.adaptation!=='run')) assert.ok(notAdapted.includes('>'+e(m.name)+'<')&&notAdapted.includes(e(say(m.adaptation,label).text)),where+': '+m.name+' not adapted, with the reason');
    }
  }

  // 2. The home page's per-protocol table: the embedded rows are the CSVs' at the precision printed,
  //    the first paint equals the script's render, and the script carries every caveat.
  const round=(v,d)=>Number(Number(v).toFixed(d));
  for(const label of ['en','zh']){
    const J=JSON.parse(fmEmbedded(label));
    assert.equal(J.release,REL,label+': the embedded rows name their release');
    for(const t of data.tracks){
      const rows=csvOf(t.id),T=J.tracks[t.id];
      assert.equal(T.file,'foundation-models-'+t.id+'.csv',label+'/'+t.id+': the embedded rows\' file');
      assert.deepEqual(T.rows.map(r=>r.id),F.models.map(m=>m.id),label+'/'+t.id+': one embedded row per checkpoint, in order');
      for(const r of T.rows){
        const rec=rows.find(x=>x.model_id===r.id),m=F.models.find(x=>x.id===r.id),xc=xcell(XKEY[r.id],t.id),w=label+'/'+t.id+'/'+r.id;
        const done=rec.status==='complete',tr=t.type==='tradeoff';
        assert.deepEqual([r.name,r.panel,r.mode,r.channels,r.status],[m.name,m.panel,rec.evaluation_mode,Number(rec.channels),done?'complete':'not_run'],w+': identity');
        assert.deepEqual([r.y,r.x,r.subjects],done?[round(rec.primary_percent,1),round(rec.secondary_value,tr?1:3),Number(rec.participants)]:[null,null,null],w+': figures at the precision printed');
        assert.deepEqual(r.interval,done&&!tr?[round(rec.descriptive_interval_low_percent,1),round(rec.descriptive_interval_high_percent,1)]:null,w+': interval');
        const c=t.chanceLevel,flag=!done||tr?null:Number(rec.primary_percent)<=c?'at-or-below':Number(rec.descriptive_interval_low_percent)<=c?'interval-reaches':null;
        assert.equal(r.chanceFlag,flag,w+': the chance flag, from the CSV\'s full values');
        assert.deepEqual([r.exposure,r.exposureText,r.exposureSource],[xc.status,statementIn(xc.statement,label),xc.urls[0]],w+': exposure');
        assert.equal(r.footnote,say(m.row_footnote,label).text,w+': footnote');
        assert.equal(r.licence,say(m.licence_note,label).text,w+': licence note');
        assert.equal(r.researchUse,r.id==='zuna',w+': research use');
        // Review of 2026-10-05: REVE's version where its licence asks for it; the notes in the page's language.
        assert.equal(r.version,SLUG[r.id]==='reve'?`${m.name} @ ${m.revision.split(' @ ').at(-1)}`:null,w+': the model version where the licence asks for it');
        {const c=F.frozen_probe.find(x=>x.model===r.id&&x.protocol===t.id),parts=[...m.notes,...(c.notes??[])];
         assert.deepEqual([r.notes,r.notesOriginal],label==='en'||!rec.notes?[rec.notes,null]:[parts.map(x=>Z[x]).join(''),rec.notes],w+': the notes in the page\'s language');}
        assert.equal(r.reason,done?null:say(rec.not_run_reason,label).text,w+': the reason a cell was not run');
        assert.equal(r.href,`/${label==='zh'?'zh/':''}methods/${SLUG[r.id]}/`,w+': method page');
        if(tr) assert.deepEqual(r.idle,{detected:Number(rec.commands_detected),commandTrials:Number(rec.command_trials),falseActivations:Number(rec.idle_false_activations),idleTrials:Number(rec.idle_trials),abstain:Number(rec.always_abstain_participants)},w+': idle counts');
      }
      assert.equal(T.coreExposure.text,statementIn(E.statements.not_exposed,label),label+'/'+t.id+': LaBraM and CBraMod, the sourced statement');
      assert.deepEqual([...T.coreExposure.urls].sort(),[...new Set(['labram','cbramod'].flatMap(k=>xcell(k,t.id).urls))].sort(),label+'/'+t.id+': with their sources');
    }
    // Render every protocol as each language's page would, and open dialogs.
    const els=new Map(),g=s=>{if(!els.has(s))els.set(s,new Element());return els.get(s);};
    g('#family-filter').value='all';g('#sort-results').value='name';g('#fm-rows').textContent=fmEmbedded(label);
    const reg=[];
    vm.runInNewContext(stripTypeScriptTypes(source),{data,document:{querySelector:g,querySelectorAll:()=>[],documentElement:{lang:label==='zh'?'zh-Hans':'en'},modelContext:{registerTool:x=>reg.push(x)}},window:{addEventListener(){}},AbortController,Promise,console});
    const home=pageOf(label==='zh'?'zh/':'');
    for(const t of data.tracks){
      g('#track-tabs').events.click({target:{closest:()=>({dataset:{track:t.id}})}});
      const html=g('#result-rows').innerHTML,J=JSON.parse(fmEmbedded(label)).tracks[t.id],mx=J.rows.filter(r=>r.panel==='matrix');
      // Since 2026-10-08 (owner decision) the group heading carries no date and no version label.
      const head=label==='en'?`${mx.length} further foundation encoders, frozen`:`另外 ${mx.length} 个基础模型编码器（冻结）`;
      assert.ok(html.includes('<tr class="fm-group"><th colspan="4" scope="colgroup"><span class="fm-group-label">'+head)&&html.indexOf('fm-group')>html.lastIndexOf('<tr><td><button class="model-name" data-model="'),label+'/'+t.id+': the v9 group follows the released rows, counted');
      assert.ok(html.includes(`href="/${label==='zh'?'zh/':''}protocols/${t.id}/#foundation-v9"`),label+'/'+t.id+': the group links the protocol page\'s v9 section');
      // The count says how many of its rows were not run here, so it agrees with the protocols index's scored count (review of 2026-10-05).
      const nr=mx.filter(r=>r.status!=='complete').length,tail=label==='en'?` · ${nr} not run on this protocol`:`，其中 ${nr} 个在这个协议上未运行`;
      assert.equal(html.includes('<tr class="fm-group"><th colspan="4" scope="colgroup"><span class="fm-group-label">'+e(head+tail)+' <a'),nr>0,label+'/'+t.id+': the v9 group says how many of its rows were not run here ('+nr+')');
      for(const r of mx){
        const at=html.indexOf(`<tr class="fm-row" data-fm="${r.id}">`),row=html.slice(at,html.indexOf('</tr>',at)),w=label+' home '+t.id+'/'+r.id;
        assert.ok(at>0,w+': rendered');
        if(r.status==='complete') assert.ok(row.includes('<strong>'+r.y.toFixed(1)+'%</strong>'),w+': its figure');
        else assert.ok(row.includes('<strong>'+(label==='en'?'Not run':'未运行')+'</strong>')&&row.includes(e(r.reason))&&!/<strong>\d/.test(row),w+': not run, with its reason, no figure');
        const fl={'at-or-below':label==='en'?'At or below the ':'不高于 ','interval-reaches':label==='en'?'Interval reaches the ':'区间触及 '};
        if(r.chanceFlag) assert.ok(row.includes('<span class="flag">'+fl[r.chanceFlag]),w+': chance flag');
        else assert.ok(!/<span class="flag">(?:At or below|Interval reaches|不高于|区间触及)/.test(row),w+': flagged without cause');
        if(r.exposure==='not_exposed') assert.ok(!row.includes('fm-badge'),w+': no badge');
        else assert.ok(row.includes(`<span class="flag fm-badge" data-exposure="${r.exposure}">`),w+': exposure badge');
        assert.equal(row.includes('fm-research-use'),r.researchUse,w+': research-use sentence with ZUNA 1.1 only');
      }
      const ab=g('#ablation-rows').innerHTML;
      assert.deepEqual([...ab.matchAll(/<tr class="fm-row" data-fm="([^"]+)">/g)].map(m=>m[1]).sort(),[F.masking_ablation.checkpoints[0],...ablation.map(m=>m.id)].sort(),label+'/'+t.id+': the ablation panel');
      assert.equal(g('#download-fm').href,'/data/foundation-models-'+t.id+'.csv',label+'/'+t.id+': the v9 CSV download follows the protocol');
      // Follow-up review of 2026-10-05: the weights terms under the v9 rows link this protocol's full list.
      assert.equal(g('#fm-terms-link').href,(label==='zh'?'/zh':'')+'/protocols/'+t.id+'/#v9-licences',label+'/'+t.id+': the weights terms link follows the protocol');
      // The protocol dialog: the dated LaBraM/CBraMod statement after the released sentence.
      g('#open-protocol').events.click();
      const dlg=g('#dialog-body').innerHTML;
      assert.ok(dlg.indexOf('fm-core-exposure')>dlg.indexOf(e(t.pretrainingOverlap))&&dlg.includes(e(statementIn(E.statements.not_exposed,label)))
        &&J.coreExposure.urls.every(u=>dlg.includes(`href="${u}"`)),label+'/'+t.id+': the protocol dialog carries the sourced statement beside the released one');
      g('#close-dialog').events.click();
      // The first paint is the script's render of the first protocol.
      if(t.id===data.tracks[0].id){
        // The v9 group only: the released rows' first paint keeps the payload's order, the script sorts by name.
        const s0=home.indexOf('<tbody id="result-rows">'),staticRows=home.slice(s0+24,home.indexOf('</tbody>',s0));
        const fromGroup=x=>x.slice(x.indexOf('<tr class="fm-group">'));
        assert.equal(textOf(fromGroup(staticRows)),textOf(fromGroup(html)),label+': the first paint of the v9 group equals the script\'s render');
        const a0=home.indexOf('<tbody id="ablation-rows">'),staticAbl=home.slice(a0+26,home.indexOf('</tbody>',a0));
        assert.equal(textOf(staticAbl),textOf(ab),label+': the first paint of the ablation panel equals the script\'s render');
      }
    }
    // A v9 row's dialog: figures, exposure with source, footnote, licence (research use), links.
    g('#track-tabs').events.click({target:{closest:()=>({dataset:{track:'mi-rest'}})}});
    g('#result-rows').events.click({target:{closest:()=>({dataset:{model:'fm:zuna'}})}});
    const z=JSON.parse(fmEmbedded(label)).tracks['mi-rest'].rows.find(r=>r.id==='zuna'),zd=g('#dialog-body').innerHTML;
    for(const s of [z.exposureText,z.footnote,z.licence,research[label]]) assert.ok(zd.includes(e(s)),label+': the ZUNA 1.1 dialog carries "'+s.slice(0,40)+'"');
    // The script's own words carry no date and no version label either (owner decision 2026-10-08).
    assert.ok(!/\bv9\b|第九轮|新增|\b[Aa]dded\b|20\d\d-\d\d-\d\d/.test(visible(zd))&&!/\bv9\b|第九轮|新增|\b[Aa]dded\b/.test(visible(g('#result-rows').innerHTML)),label+': the rendered rows and dialog state no date or version label');
    assert.ok(zd.includes(`href="${z.exposureSource}"`)&&zd.includes('#foundation-v9')&&zd.includes(`href="${z.href}"`)&&g('#detail-dialog').open,label+': the dialog links the source, the section and the method page');
    g('#close-dialog').events.click();
    // REVE's dialog names the model version its licence asks for.
    g('#result-rows').events.click({target:{closest:()=>({dataset:{model:'fm:reve-large'}})}});
    assert.ok(g('#dialog-body').innerHTML.includes((label==='en'?'Model version: ':'模型版本：')+(label==='en'?'<span>':'<span lang="en">')+e(reveVersions.split(' · ')[1])+'</span>'),label+': the REVE Large dialog names its version');
    g('#close-dialog').events.click();
    // The note under the snapshot, and the lede: the count of what they point at.
    const added=home.slice(home.indexOf('<p class="matrix-added"'),home.indexOf('</p>',home.indexOf('<p class="matrix-added"')));
    assert.ok(added.includes(`data-release="${REL}"`)&&added.includes(label==='en'?`${matrix.length} further foundation encoders`:`另外 ${matrix.length} 个基础模型编码器`),label+': the snapshot note counts the v9 matrix rows');
    assert.ok(added.includes(label==='en'?'not ranked against it':'也不与它排名'),label+': the v9 rows are not ranked against the snapshot');
    // Follow-up review of 2026-10-05: the release log and data use count eleven models and sixteen checkpoints; the note
    // says what the 13 encoders are, from the export (the models evaluated in v9, the masking ablation's siblings).
    {const models=E.models.filter(m=>m.evaluated_in_v9).length,abl=F.models.filter(m=>m.panel==='masking ablation').length;
     assert.ok(models===11&&abl===3&&matrix.length+abl===F.models.length,'v9: eleven models, three ablation siblings, sixteen checkpoints');
     assert.ok(added.includes(label==='en'?`They are checkpoints of ${models} models; ${abl} more checkpoints of one of them form a masking ablation, ${matrix.length+abl} in all.`
       :`它们是 ${models} 个模型的检查点；其中一个模型另有 ${abl} 个检查点组成掩码消融，共 ${matrix.length+abl} 个。`),label+': the snapshot note says the encoders are checkpoints of '+models+' models, '+(matrix.length+abl)+' with the ablation');}
    // The weights terms of every v9 checkpoint under the table, as on the dataset pages: each licence, REVE named by
    // version, no endorsement, and the protocol page's full list linked (the first protocol on first paint).
    {const t0=home.indexOf('<p class="fm-terms-home" id="fm-terms">'),terms=home.slice(t0,home.indexOf('</p>',t0));
     assert.ok(t0>0&&t0>home.indexOf('id="download-fm"')&&t0<home.indexOf('id="ablation-panel"'),label+': the weights terms sit under the v9 rows, before the ablation panel');
     for(const x of F.models) assert.ok(terms.includes(label==='zh'&&/^REVE /.test(licName(x))?'REVE 负责任使用许可 v1.0':licName(x)),label+': the home terms name '+x.name+'\'s licence');
     assert.ok(terms.includes(F.models.filter(x=>SLUG[x.id]==='reve').map(x=>`${x.name} @ ${x.revision.split(' @ ').at(-1)}`).join(' · ')),label+': the home terms name REVE by version');
     assert.ok(terms.includes(endorse[label])&&terms.includes(`id="fm-terms-link" href="/${label==='zh'?'zh/':''}protocols/${data.tracks[0].id}/#v9-licences"`),label+': no endorsement, and the full list linked');}
    // "On the same eight protocols", with the encoder that ran on fewer named and counted (BrainOmni Base: six).
    for(const m of matrix){const ran=F.frozen_probe.filter(c=>c.model===m.id&&c.status==='complete').length;
      if(ran<data.tracks.length) assert.ok(added.includes(label==='en'?`${e(m.name)} on ${['zero','one','two','three','four','five','six','seven'][ran]} of them`:`${e(m.name)} 只在其中 ${ran} 个上运行`),label+': the snapshot note says '+m.name+' ran on '+ran+' protocols');}
    assert.doesNotMatch(home,/Best on that protocol|该协议最佳/,label+': the snapshot\'s key names whose highest score it marks');
  }

  // 3. The model directory and the methods hub.
  for(const [label,prefix] of [['en',''],['zh','zh/']]){
    const html=pageOf(prefix+'methods/'),where=prefix+'methods/';
    const statusZh={'Evaluated':'已评测','Evaluated (6 of 8 protocols)':'已评测（8 个协议中的 6 个）','Evaluated (frozen probes, masking ablation)':'已评测（冻结探针，掩码消融）',
      'Evaluated (frozen probes)':'已评测（冻结探针）','Catalogue only (not evaluated)':'仅列入目录（未评测）'};
    const entries=F.directory_status.filter(x=>!['REVE Base','EEGPT'].includes(x.name)).flatMap(x=>/, /.test(x.name)&&!/\(/.test(x.name)?x.name.split(', ').map(n=>({...x,name:n})):[x]);
    const members={'REVE Large':['reve-large'],'LUNA (Base, Large)':['luna-base','luna-large'],'BrainOmni Base':['brainomni-base'],CodeBrain:['codebrain'],EEGMamba:['eegmamba'],
      'ST-EEGFormer (Base, Large)':['steegformer-base','steegformer-large'],'eeg-fm-masking (4 checkpoints)':F.masking_ablation.checkpoints,'ERP-FM Base':['erp-fm-base'],SingLEM:['singlem'],'ZUNA 1.1':['zuna'],MIRepNet:[],'EEG-DINO':[]};
    assert.deepEqual(entries.map(x=>x.name).sort(),Object.keys(members).sort(),where+': one card per directory entry the export suggests');
    for(const x of entries){
      const a=html.indexOf(`<article class="model-card" data-model="${e(x.name)}" data-release="${REL}">`),card=html.slice(a,html.indexOf('</article>',a)),w=where+' '+x.name;
      assert.ok(a>0,w+': card');
      assert.ok(card.includes('>'+(label==='en'?x.suggested_status:statusZh[x.suggested_status])+'</span>'),w+': the status the export suggests');
      assert.ok(card.includes(`<time datetime="2026-10-04">`),w+': when its status was checked');
      const ms=members[x.name].map(id=>F.models.find(m=>m.id===id));
      if(ms.length){
        assert.ok(card.includes(`href="/${prefix}methods/${SLUG[ms[0].id]}/"`),w+': its method page');
        for(const v of new Set(ms.map(m=>m.parameters_encoder))) assert.ok(card.includes(`data-fig="${FMJ}|m2|${v}"`),w+': encoder parameters '+v);
        assert.ok(printed(card,ms[0].weights_licence,label),w+': weights licence');
        if(ms[0].licence_note.replace(/\.$/,'')!==ms[0].weights_licence) assert.ok(printed(card,ms[0].licence_note,label),w+': licence note');
      } else assert.ok(!card.includes('data-fig')&&!/<a href="\/(?:zh\/)?methods\//.test(card),w+': a catalogue-only card has no figure and no page');
    }
    const card=n=>html.slice(html.indexOf(`data-model="${n}"`),html.indexOf('</article>',html.indexOf(`data-model="${n}"`)));
    assert.match(card('ZUNA 1.1'),label==='en'?/research use only, not for diagnosis or clinical use/:/仅供研究使用，不可用于诊断或临床/,where+': ZUNA 1.1\'s research-use sentence');
    assert.match(card('LUNA (Base, Large)'),label==='en'?/no implied endorsement by the LUNA authors/:/不代表 LUNA 作者的认可/,where+': LUNA\'s no-endorsement note');
    assert.match(card('ERP-FM Base'),label==='en'?/non-commercial/:/非商业/,where+': ERP-FM is non-commercial');
    assert.match(card('EEGPT'),label==='en'?/<span class="status">Rights review pending<\/span>/:/<span class="status">权利审查中<\/span>/,where+': EEGPT is unchanged');
    const un=html.slice(html.indexOf('id="unmeasured"'),html.indexOf('</ul>',html.indexOf('id="unmeasured"')));
    for(const [id,n] of [['mirepnet','MIRepNet'],['eeg-dino','EEG-DINO']]) assert.ok(un.includes(`<li id="${id}"><span lang="en">${n}</span>`)&&un.includes(label==='en'?'Catalogue only (not evaluated)':'仅列入目录（未评测）'),where+': '+n+' is catalogue only');
    assert.ok(!un.includes('REVE Base'),where+': REVE Base is evaluated, not unmeasured');
    const table=html.slice(html.indexOf('id="with-pages"'),html.indexOf('</table>',html.indexOf('id="with-pages"')));
    for(const s of slugs) assert.ok(table.includes(`href="/${prefix}methods/${s}/"`),where+': the '+s+' page is listed');
  }

  // 4. Method pages: groups, checkpoints and terms, exposure; the Measured-on line on every one.
  const methodPages=entityPages.filter(f=>/^(?:zh\/)?methods\/[^/]+\/index\.html$/.test(f));
  for(const f of methodPages){
    const html=readFileSync(new URL(f,DIST),'utf8'),zh=f.startsWith('zh/'),prefix=zh?'zh/':'',path=f.replace(/index\.html$/,'');
    const at=html.indexOf('<p class="entity-measured">'),line=html.slice(at,html.indexOf('</p>',at));
    assert.ok(at>html.indexOf('class="topic-hero"')&&at<html.indexOf('id="results-heading"'),path+': the Measured-on line sits under the hero');
    // A group with no table (a checkpoint not run there) measured nothing and is not on the line.
    // A BOAS group (route 2, 2026-10-07) is marked data-boas, the region its three gaps hold.
    const groups=[...html.matchAll(/<section class="entity-group" id="g-[^"]+"(?: data-boas="true")?>\s*<h3><a href="([^"]+)"[\s\S]*?<p class="entity-group-meta">[^<]*<a href="([^"#]+)[\s\S]*?<\/section>/g)].filter(g=>g[0].includes('<tbody>'));
    const want=[...new Set(groups.map(g=>g[1])),...new Set(groups.map(g=>g[2]).filter(h=>/\/protocols\//.test(h)))];
    assert.deepEqual([...line.matchAll(/href="([^"]+)"/g)].map(m=>m[1]).sort(),[...new Set(want)].sort(),path+': the line links exactly the dataset and protocol pages its groups are read on');
    assert.match(line,zh?/测量所用数据集：/:/Measured on:/,path+': the line says what it lists');
    const md=readFileSync(new URL(path+'index.md',DIST),'utf8');
    for(const h of new Set(want)) assert.ok(md.includes('](https://bci.report'+h+')'),path+'index.md: the Measured-on line survives ('+h+')');
  }
  for(const s of slugs) for(const [label,prefix] of [['en',''],['zh','zh/']]){
    const path=prefix+'methods/'+s+'/',html=pageOf(path),ms=F.models.filter(m=>SLUG[m.id]===s);
    for(const t of data.tracks){
      const ds=MVPSLUG[t.dataset],gid=`g-${ds}-${t.id}-foundation-v9`,a=html.indexOf(`id="${gid}"`),grp=html.slice(a,html.indexOf('</section>',a));
      const scored=ms.filter(m=>F.frozen_probe.find(c=>c.model===m.id&&c.protocol===t.id).status==='complete'),missing=ms.filter(m=>!scored.includes(m));
      assert.ok(a>0&&grp.includes(`href="/${prefix}protocols/${t.id}/#foundation-v9"`),path+': the '+t.id+' group, read with the protocol page\'s v9 section');
      assert.equal(bodyRows(grp),scored.length*(t.type==='tradeoff'?2:1),path+': '+t.id+' rows');
      for(const m of missing) assert.ok(grp.includes('fm-not-run-note')&&printed(grp,F.frozen_probe.find(c=>c.model===m.id&&c.protocol===t.id).reason,label),path+': '+m.name+' on '+t.id+' is not run, with its reason');
    }
    const adapted=ms.filter(m=>m.adaptation==='run');
    assert.equal(html.includes('id="g-eegmat-eegmat-v9-adaptation"'),adapted.length>0,path+': the EEGMAT adaptation group where the model was adapted');
    for(const g of [...html.matchAll(/<section class="entity-group" id="(g-[^"]+-(?:foundation-v9|v9-adaptation))">([\s\S]*?)<\/section>/g)].filter(g=>g[2].includes('<tbody>'))){
      termsOk(g[2],label,prefix,path+' '+g[1]);
      if(s==='zuna') zunaRowsOk(g[2],label,path+' '+g[1],g[1].endsWith('v9-adaptation'));
    }
    const cp=html.slice(html.indexOf('<section class="topic-section" id="checkpoints"'),html.indexOf('</section>',html.indexOf('id="checkpoints"')));
    for(const m of ms){
      const a=cp.indexOf(`<article class="fm-checkpoint" data-checkpoint="${m.id}">`),art=cp.slice(a,cp.indexOf('</article>',a)),w=path+' '+m.id;
      assert.ok(a>=0,w+': its checkpoint entry');
      assert.ok(art.includes(`data-fig="${FMJ}|m2|${m.parameters_encoder}"`),w+': encoder parameters');
      if(m.revision) assert.ok(art.includes('<code>'+e(m.revision)+'</code>')&&art.includes(m.checkpoint_sha256),w+': revision and checkpoint hash');
      else assert.match(art,label==='zh'?/发布中没有记录/:/Not in the release/,w+': a revision the release does not name is said to be missing');
      for(const x of [m.weights_licence,m.rights_review,m.row_footnote,...m.notes]) assert.ok(printed(art,x,label),w+': "'+x.slice(0,40)+'"');
      assert.equal(art.includes(research[label]),m.id==='zuna',w+': the research-use sentence with ZUNA 1.1');
      if(m.adaptation!=='run') assert.ok(printed(art,m.adaptation,label),w+': why it was not adapted');
    }
  }
  // Exposure, by dataset: the v9 families and LaBraM and CBraMod, from the exposure table.
  for(const s of [...slugs,'labram','cbramod']) for(const [label,prefix] of [['en',''],['zh','zh/']]){
    const path=prefix+'methods/'+s+'/',html=pageOf(path),sec=html.slice(html.indexOf('id="pretraining-exposure"'),html.indexOf('</section>',html.indexOf('id="pretraining-exposure"')));
    const keys=s==='labram'||s==='cbramod'?[s]:[...new Set(F.models.filter(m=>SLUG[m.id]===s).map(m=>XKEY[m.id]))];
    assert.ok(sec.includes(label==='en'?'checked on 2026-10-04':'于 2026-10-04 核查'),path+': the exposure section says when it was checked');
    const trs=[...sec.matchAll(/<tr data-exposure="([^"]+)">([\s\S]*?)<\/tr>/g)];
    const tables=(sec.match(/<table class="fm-exposure-table">/g)||[]).length;
    assert.equal(trs.length,7*tables,path+': seven datasets per table');
    for(const k of keys) for(const d of E.datasets){
      const c=E.cells.find(x=>x.model===k&&x.dataset===d.key);
      const tr=trs.find(x=>x[2].includes(`href="${d.url}"`)&&x[1]===c.status&&x[2].includes(e(statementIn(c.statement,label))));
      assert.ok(tr,path+': '+k+' on '+d.key+': the statement');
      const hrefs=[...tr[2].slice(tr[2].lastIndexOf('<td>')).matchAll(/href="([^"]+)"/g)].map(x=>decodeHtml(x[1]));
      assert.deepEqual(hrefs,c.urls,path+': '+k+' on '+d.key+': its sources');
      if(c.status!=='not_exposed') assert.ok(tr[2].includes(`<span class="flag fm-badge" data-exposure="${c.status}">`),path+': '+k+' on '+d.key+': badge');
    }
    if(s==='zuna') assert.ok(trs.every(x=>x[1]==='unknown'),path+': ZUNA 1.1 is unknown everywhere');
    // The exposure table's caveats that name the model are printed with it.
    for(const c of E.caveats.filter(c=>c.includes(NAME[s]))) assert.ok(printed(sec,c,label),path+': the caveat "'+c.slice(0,40)+'"');
    const vis=visible(label==='zh'?chineseOnly(sec):sec);
    assert.doesNotMatch(vis,notProof[label],path+': no exposure claim beyond the authors\' lists');
  }

  // 5. Dataset pages: a v9 group per core protocol beside the released one; EEGMAT the adaptation.
  for(const t of data.tracks) for(const prefix of ['','zh/']){
    const ds=MVPSLUG[t.dataset],path=prefix+'datasets/'+ds+'/',html=pageOf(path);
    const a=html.indexOf(`id="g-${t.id}-foundation-v9"`),grp=html.slice(a,html.indexOf('</section>',a));
    const scored=F.frozen_probe.filter(c=>c.protocol===t.id&&c.status==='complete').length;
    assert.ok(a>html.indexOf(`id="g-${t.id}"`)&&grp.includes(`href="/${prefix}protocols/${t.id}/#foundation-v9"`),path+': the '+t.id+' v9 group follows the released one and links the v9 section');
    assert.equal(bodyRows(grp),scored*(t.type==='tradeoff'?2:1),path+': every scored checkpoint');
    assert.equal(grp.includes('fm-not-run-note'),scored<F.models.length,path+': a checkpoint not run is named with its reason');
    const label=prefix?'zh':'en';
    zunaRowsOk(grp,label,path+' '+t.id+' v9 group',false);
    termsOk(grp,label,prefix,path+' '+t.id+' v9 group');
  }
  for(const prefix of ['','zh/']){
    const html=pageOf(prefix+'datasets/eegmat/'),a=html.indexOf('id="g-eegmat-v9-adaptation"'),grp=html.slice(a,html.indexOf('</section>',a));
    assert.equal(bodyRows(grp),3*F.eegmat_adaptation.rows.length,prefix+'datasets/eegmat/: the v9 adaptation, three rows per adapted encoder');
    zunaRowsOk(grp,prefix?'zh':'en',prefix+'datasets/eegmat/ v9 adaptation',true);
    termsOk(grp,prefix?'zh':'en',prefix,prefix+'datasets/eegmat/ v9 adaptation');
  }

  // 6. LaBraM and CBraMod on the topic pages and data use: the sourced statement, never "unresolved".
  for(const [slug,models] of [['does-pretraining-help',['labram','cbramod']],['model-adaptation',['labram']]]) for(const [label,prefix] of [['en',''],['zh','zh/']]){
    const path=prefix+'topics/'+slug+'/',html=pageOf(path);
    assert.doesNotMatch(visible(html),label==='en'?/unresolved|not certified|unseen during pretraining/i:/尚不能确定这些基准|无法证实|重叠尚不清楚|未曾出现/,path+': the old exposure wording is gone');
    assert.ok(visible(html).includes(label==='en'?'published pretraining list':'公开的预训练数据清单'),path+': the authors\' published list');
    assert.ok(visible(html).includes(label==='en'?'not proof that':'并不证明'),path+': which is not a proof');
    const note=html.slice(html.indexOf('fm-core-exposure'),html.indexOf('</p>',html.indexOf('fm-core-exposure')));
    assert.ok(note.includes('2026-10-04'),path+': the check date');
    for(const k of models) for(const u of new Set(E.cells.filter(c=>c.model===k).flatMap(c=>c.urls))) assert.ok(note.includes(`href="${u}"`),path+': '+k+'\'s source '+u);
  }
  const dataUse=pageOf('data-use/');
  assert.ok(!dataUse.includes('Pretraining overlap remains unknown')&&dataUse.includes('not in the authors’ published pretraining list'),'data-use/: the sourced statement replaces "overlap remains unknown"');

  // 7. Hubs and the release log count and name what they lead to.
  for(const [label,prefix] of [['en',''],['zh','zh/']]){
    const index=pageOf(prefix+'protocols/');
    for(const t of data.tracks){
      const tr=index.slice(index.indexOf(`<tr data-protocol="${t.id}">`),index.indexOf('</tr>',index.indexOf(`<tr data-protocol="${t.id}">`)));
      const n=csvOf(t.id).filter(r=>r.panel==='matrix'&&r.status==='complete').length;
      const m=tr.match(/<small class="fm-count"><a href="([^"]+)">([^<]+)<\/a><\/small>/);
      assert.ok(m&&m[1]===`/${prefix}protocols/${t.id}/#foundation-v9`&&m[2].includes(label==='en'?`+ ${n} further foundation encoders`:`另有 ${n} 个基础模型编码器`),prefix+'protocols/: '+t.id+' counts the v9 rows it links to ('+n+')');
    }
    const rel=pageOf(prefix+'releases/'),entry=rel.slice(rel.indexOf(`id="${REL}"`),rel.indexOf('</article>',rel.indexOf(`id="${REL}"`)));
    for(const p of ['protocols','methods']) assert.ok(entry.includes(`href="/${prefix}${p}/"`),prefix+'releases/: the v9 release names the '+p+' hub');
    assert.doesNotMatch(entry,/Core matrix \(home page\)|核心矩阵（首页）/,prefix+'releases/: a hub is not the home page');
    if(label==='en'){const feed=readFileSync(new URL('releases.xml',DIST),'utf8'),fe=feed.slice(feed.indexOf(`<id>https://bci.report/releases/#${REL}</id>`),feed.indexOf('</entry>',feed.indexOf(`#${REL}</id>`)));
      assert.ok(fe.includes('&lt;a href=&quot;https://bci.report/protocols/&quot;&gt;Protocols&lt;/a&gt;')&&!fe.includes('Core matrix (home page)'),'releases.xml: the v9 entry names the hubs as the release log does');}
  }
  // The EESM19 page changed again on 2026-10-07 (route 2's group), so it carries that date now; does-pretraining-help
  // on 2026-10-08 (its pointer to the later-sessions question).
  for(const p of ['protocols/mi-rest/','protocols/','methods/','methods/reve/','methods/labram/','datasets/eegmat/','datasets/eesm19/','topics/does-pretraining-help/']){
    const d=p==='datasets/eesm19/'?'2026-10-07':p==='topics/does-pretraining-help/'?'2026-10-08':'2026-10-04';
    assert.ok(sitemap.includes(`<loc>https://bci.report/${p}</loc><lastmod>${d}</lastmod>`),'sitemap: '+p+' changed on '+d);}
}
// --- 2026-10-04 v9 foundation models: the topics ----------------------------------------------------
// The v9 findings on the questions (owner approval 2026-10-04): does-pretraining-help gains #v9-encoders —
// sleep (the new rows above every released one), BETA (above CBraMod, not above training-free CCA), the EEGMAT
// adaptation (one fixed recipe on one task, not a ranking; LoRA budgets differ), REVE Base against Large
// (marginal intervals, no paired test) and the masking ablation — and fewer-electrodes gains #v9-montage, BETA
// at eight and four electrodes beside the released rows and the six-channel sleep column; model-adaptation
// points to the adaptation table without a figure. Every figure in the two sections is a data-fig re-read by
// the topic loop above; pinned here: each figure is a leaf of the v9 JSON, the protocol's v9 CSV or
// experiments.json and sits on a row naming its protocol; every figure-like token is one of those values as the
// site prints it; the same figures in both languages; rows in the export's family order; each relation word
// the export's; chance flags by the core rule; exposure badges and ZUNA 1.1's research-use sentence; every claim
// the prose makes is the one the export supports; no ranking word and no exposure claim beyond the lists.
{
  const REL='foundation-models-update-20261004', FMJ='foundation-models-update.json';
  const FX=JSON.parse(readFileSync(new URL('data/'+FMJ,DIST),'utf8')),F=FX.results['foundation-models-v9'],C=F.comparisons;
  const MVPJ=JSON.parse(readFileSync(new URL('data/experiments.json',DIST),'utf8'));
  const csvOf=p=>{const [h,...b]=csvRows(readFileSync(new URL('data/foundation-models-'+p+'.csv',DIST),'utf8')).filter(r=>r.length>1);return b.map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i]])));};
  const cell=(p,id)=>csvOf(p).find(r=>r.model_id===id);
  const coreRow=(t,id)=>MVPJ.tracks.find(x=>x.id===t).rows.find(r=>r.id===id);
  const name=id=>F.models.find(m=>m.id===id).name;
  const matrix=F.models.filter(m=>m.panel==='matrix').map(m=>m.id),siblings=F.models.filter(m=>m.panel!=='matrix').map(m=>m.id);
  const scored=C.masking_ablation.map(x=>x.protocol);
  const e=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const zhSrc=stripTypeScriptTypes(readFileSync(new URL('../src/data/foundation-models-zh.ts',import.meta.url),'utf8')).replace(/^import[^\n]*\n/gm,'').replace(/^export /gm,'');
  const zhCtx={};vm.runInNewContext(zhSrc+'\nthis.fmZh=fmZh;',zhCtx);const Z=zhCtx.fmZh;
  const research={en:'Model card: research use only, not for diagnosis or clinical use.',zh:'模型卡：仅供研究使用，不可用于诊断或临床。'};
  // A ranking word, after the phrases that deny one (and LoRA's rank) are set aside. Since the review of 2026-10-05
  // "the best published non-foundation row" is not set aside: on BETA that row's interval overlaps EEGNet's, so the
  // pages name it by its point estimate ("highest" is not a ranking word here, "best" and "stays the highest" are).
  const ranking={en:/\b(?:best|top|winner|leader|outperform\w*|beats?|ranks?|ranked|ranking)\b|stays? the highest|keeps the highest/i,zh:/最佳|最好的|胜出|排名第|第一名|仍是最高|仍是 4 个电极上的最高分/};
  const rankingOk={en:/\b(?:not ranked|never ranked|not a ranking|none of them ranks|share a ranking)\b|rank-4|rank 4|any model’s best/gi,zh:/不排名|不是排名|从不排名|都不用来给模型排名|不能放进同一个排名/g};
  const notProof={en:/\bnot exposed\b|\bproven\b|\bno overlap\b/i,zh:/已证明|证明没有|没有重叠/};
  const flagOf=(y,lo,c)=>y<=c?'at-or-below':lo<=c?'interval-reaches':null;
  const famOf=id=>({'reve-base':'reve','reve-large':'reve','luna-base':'luna','luna-large':'luna','brainomni-base':'brainomni','steegformer-base':'st-eegformer','steegformer-large':'st-eegformer','erp-fm-base':'erp-fm'})[id]??(id.startsWith('eeg-fm-masking/')?'eeg-fm-masking':id);
  const reveVersions=F.models.filter(m=>famOf(m.id)==='reve').map(m=>`${m.name} @ ${m.revision.split(' @ ').at(-1)}`).join(' · ');
  const flagWord={en:{'at-or-below':'At or below chance level','interval-reaches':'Interval reaches chance level'},zh:{'at-or-below':'不高于随机水平','interval-reaches':'区间触及随机水平'}};
  const textOf=s=>decodeHtml(s.replace(/<[^>]+>/g,' ')).replace(/\s+/g,' ').trim();
  // Every value of the files these sections read, as the site prints it, and every number in their own text.
  const tok=new Set();
  const addVal=v=>{for(const g of fmtEarlier)for(const n of numbers(g(v)))tok.add(n);};
  const walk=v=>{if(typeof v==='number')addVal(v);else if(typeof v==='string')numbers(v).forEach(n=>tok.add(n));else if(v&&typeof v==='object')Object.values(v).forEach(walk);};
  walk(FX);walk(MVPJ);walk(Z);
  for(const p of scored.concat('idle')) for(const r of csvOf(p)) for(const v of Object.values(r)){if(v.trim()!==''&&Number.isFinite(Number(v)))addVal(Number(v));else numbers(v).forEach(n=>tok.add(n));}
  const figureLike=t=>[...t.matchAll(/\d+\.\d+|\d{1,3}(?:,\d{3})+/g)].map(m=>m[0]);
  // The extent of every element carrying an attribute: [start, end, value].
  const extents=(html,attr)=>{const out=[];for(const m of html.matchAll(new RegExp(`<(\\w+)[^>]*\\s${attr}="([^"]+)"`,'g'))){
    const tag=m[1];let depth=0,i=m.index;const re=new RegExp(`<${tag}[\\s>]|</${tag}>`,'g');re.lastIndex=i;let x;
    while((x=re.exec(html))){depth+=x[0].startsWith('</')?-1:1;if(depth===0){out.push([m.index,x.index,m[2]]);break;}}}return out;};
  const figsIn=h=>[...h.matchAll(/data-fig="([^|"]+)\|(\w+)\|([^"]+)"/g)].map(m=>({file:m[1],fmt:m[2],raw:Number(m[3]),at:m.index}));
  const sectionOf=(html,id)=>{const a=html.indexOf(`<section class="topic-section fm-topic" id="${id}"`);assert.ok(a>0,id+' must render');
    const b=html.indexOf('</section>',a);assert.equal(html.slice(a+8,b).indexOf('<section'),-1,id+' nests no section');return {a,sec:html.slice(a,b)};};
  const rowFigs=(h,file)=>figsIn(h).filter(f=>!file||f.file===file).map(f=>f.raw);
  const relOf=(id,p)=>{const x=C.vs_published_rows.find(c=>c.model===id&&c.protocol===p);return [x.labram.relation,x.cbramod.relation,x.best_non_foundation.relation];};
  const xsec={};
  for(const [label,prefix] of [['en',''],['zh','zh/']]){
    const zh=label==='zh',W=flagWord[label];
    // --- Shared to both sections: files, rows, tokens, words. ---
    const common=(path,id)=>{
      const html=pageOf(path),{a,sec}=sectionOf(html,id),w=path+'#'+id;
      assert.ok(sec.includes(`data-release="${REL}"`),w+': names its release');
      const figs=figsIn(sec);
      assert.ok(figs.length>40,w+': prints its figures ('+figs.length+')');
      assert.ok(figs.every(f=>f.file===FMJ||/^foundation-models-[a-z0-9-]+\.csv$/.test(f.file)||f.file==='experiments.json'),w+': every figure from the v9 JSON, a v9 CSV or experiments.json');
      // A protocol's row figure sits on an element naming that protocol and the row.
      const fmX=extents(sec,'data-fm-topic'),coreX=extents(sec,'data-core-topic');
      for(const f of figs){
        if(f.file===FMJ) continue;
        const hit=(f.file==='experiments.json'?coreX:fmX).filter(([s,t])=>s<=f.at&&f.at<=t);
        assert.ok(hit.length,w+': '+f.file+' '+f.raw+' is printed on no row that names its protocol');
        const [track,rid]=hit.at(-1)[2].split('|');
        if(f.file==='experiments.json') assert.ok(Object.values(coreRow(track,rid)).flat().includes(f.raw),w+': '+f.raw+' is not a value of the released '+track+' / '+rid+' row');
        else {assert.equal(f.file,'foundation-models-'+track+'.csv',w+': '+f.raw+' sits on a '+track+' row but comes from '+f.file);
              assert.ok(Object.values(cell(track,rid)).map(Number).includes(f.raw),w+': '+f.raw+' is not a value of '+rid+' on '+track);}
      }
      const vis=visible(zh?chineseOnly(sec):sec);
      for(const t of figureLike(visible(sec))) assert.ok(tok.has(t),w+': "'+t+'" is not a value of the files this section reads');
      assert.doesNotMatch(vis.replace(rankingOk[label],' '),ranking[label],w+': no ranking word');
      assert.doesNotMatch(vis,notProof[label],w+': no exposure claim beyond the authors\' lists');
      // Exposure badges: a v9 cell's badge is its exposure table status; ZUNA 1.1's rows carry the research-use sentence.
      for(const [s,t,v] of fmX){
        const [track,rid]=v.split('|'),h=sec.slice(s,t),st=cell(track,rid).pretraining_exposure,c=F.frozen_probe.find(x=>x.model===rid&&x.protocol===track).exposure.status;
        if(/^<(?:td|tr)\b/.test(sec.slice(s,s+4))){
          if(c==='exposed') assert.ok(h.includes('<span class="flag fm-badge" data-exposure="exposed">'+e(zh?Z[st]:st)+'</span>'),w+': '+v+' carries its exposure badge');
          else if(c==='unknown') assert.ok(h.includes('<span class="flag fm-badge" data-exposure="unknown">'+(zh?'是否出现在预训练数据中：未知':'Exposure unknown')+'</span>'),w+': '+v+' is marked exposure unknown');
          else assert.ok(!h.includes('fm-badge'),w+': '+v+' is not in the list and carries no badge');
        }
      }
      const zunaRows=[...sec.matchAll(/<tr([^>]*data-(?:fm-topic|montage-row|adapt-row)="(?:[^"|]*\|)?zuna"[\s\S]*?)<\/tr>/g)];
      assert.ok(zunaRows.length>0,w+': ZUNA 1.1 has rows');
      for(const [,row] of zunaRows) assert.ok(row.includes(research[label]),w+': ZUNA 1.1\'s research-use sentence travels with its row');
      // Only ZUNA 1.1's rows carry it.
      assert.equal((sec.match(new RegExp(research[label].replace(/[.()]/g,'\\$&'),'g'))||[]).length,zunaRows.length,w+': the research-use sentence belongs to ZUNA 1.1\'s rows');
      assert.ok(sec.includes(label==='en'?'not proof that the recordings were never seen':'并不证明这些记录从未被模型见过'),w+': the exposure key says what a statement is not');
      assert.ok(sec.includes(`href="/data/${FMJ}" download`),w+': the v9 JSON is linked');
      // Chance flags by the core rule, wherever a balanced accuracy is printed with its interval.
      let flagged=0;
      for(const m of sec.matchAll(/data-fig="([^|"]+)\|(pct1raw|pct1)\|([^"]+)"[^>]*>[^<]*<\/span><span class="interval"><span data-fig="[^|"]+\|\w+\|([^"]+)"[^>]*>[^<]*<\/span>–<span data-fig="[^"]+">[^<]*<\/span><\/span>((?:<span class="flag">[^<]*<\/span>)?)/g)){
        const [,file,f,y,lo,flagHtml]=m;
        const chance=file===FMJ?F.eegmat_adaptation.chance_level:file==='experiments.json'?null:Number(csvOf(file.replace(/^foundation-models-|\.csv$/g,'')).find(r=>r.chance_level_percent!=='').chance_level_percent);
        const track=file==='experiments.json'?(()=>{const x=coreX.filter(([s,t])=>s<=m.index&&m.index<=t).at(-1);return x[2].split('|')[0];})():null;
        const c=chance??(track&&MVPJ.tracks.find(t=>t.id===track).chanceLevel);
        const want=flagOf(Number(y),Number(lo),c);
        assert.equal(flagHtml,want?`<span class="flag">${W[want]}</span>`:'',w+': '+file+' '+y+' carries the chance flag the core rule gives ('+want+')');
        flagged++;
      }
      // Every balanced accuracy printed with its interval in a table cell was read by the flag check above.
      assert.equal(flagged,(sec.match(/<span class="interval"><span data-fig="[^"|]+\|pct1(?:raw)?\|/g)||[]).length,w+': every balanced accuracy with an interval is checked for its chance flag');
      assert.ok(flagged>=50,w+': the chance-flag check read the tables ('+flagged+')');
      let badges=0;for(const [s,t,v] of fmX) if(/^<(?:td|tr)\b/.test(sec.slice(s,s+4))) badges++;
      assert.ok(badges>=13,w+': exposure checked on every v9 table cell ('+badges+')');
      return {html,sec,vis,figs,w};
    };

    // --- does-pretraining-help #v9-encoders ---
    {
      const {html,sec,vis,figs,w}=common(prefix+'topics/does-pretraining-help/','v9-encoders');
      xsec[label+'P']=figs.map(f=>f.file+'|'+f.raw);
      const pos=html.indexOf('id="v9-encoders"');
      assert.ok(pos>html.indexOf('id="seed-heading"')&&pos<html.indexOf('id="methods-and-limits"'),w+': after the controls, before their methods and limits');
      // Sleep: every matrix row in the export's order with the export's relations; the claim names exactly the rows above all three.
      const relText=(rels,best)=>{const refs=[['LaBraM',rels[0]],['CBraMod',rels[1]],[best,rels[2]]];
        const list=xs=>zh?xs.join('、'):xs.length<3?xs.join(' and '):xs.slice(0,-1).join(', ')+' and '+xs.at(-1);
        if(refs.every(r=>r[1]===refs[0][1])) return zh?{above:'高于三者',overlap:'与三者都重叠',below:'低于三者'}[refs[0][1]]:({above:'Above',overlap:'Overlaps',below:'Below'})[refs[0][1]]+' all three';
        const parts=['above','overlap','below'].map(r=>[r,refs.filter(x=>x[1]===r).map(x=>x[0])]).filter(([,xs])=>xs.length);
        const t=parts.map(([r,xs],i)=>zh?(r==='overlap'?`与${list(xs)}重叠`:`${{above:'高于',below:'低于'}[r]}${list(xs)}`):`${i?{above:'above',overlap:'overlaps',below:'below'}[r]:{above:'Above',overlap:'Overlaps',below:'Below'}[r]} ${list(xs)}`).join(zh?'；':'; ');
        return zh?t.replace(/([一-鿿])([A-Za-z0-9])/g,'$1 $2').replace(/([A-Za-z0-9%)])([一-鿿])/g,'$1 $2'):t;};
      for(const [track,best] of [['sleep-scalp',zh?'spectral ridge':'spectral ridge'],['beta-8ch',zh?'标准 CCA':'standard CCA']]){
        const rows=[...sec.matchAll(new RegExp(`<tr data-fm-topic="${track}\\|([^"]+)" data-rel="([^"]+)">([\\s\\S]*?)<\\/tr>`,'g'))];
        assert.deepEqual(rows.map(m=>m[1]),matrix,w+': '+track+' rows, every matrix checkpoint in the export\'s order, never sorted');
        for(const [,id,rel,row] of rows){
          const c=cell(track,id);
          assert.equal(rel,relOf(id,track).join(' '),w+': '+track+'/'+id+' relations are the export\'s');
          assert.ok(row.includes('<td class="fm-rel">'+e(relText(relOf(id,track),best))+'</td>'),w+': '+track+'/'+id+' reads its relations as "'+relText(relOf(id,track),best)+'"');
          assert.deepEqual(rowFigs(row),[c.primary_percent,c.descriptive_interval_low_percent,c.descriptive_interval_high_percent].map(Number),w+': '+track+'/'+id+' prints its CSV row');
        }
      }
      // The key under each table names the published non-foundation row the relations are read against by its point
      // estimate, never as the best; where its interval overlaps another released non-foundation row's, it says so.
      const keys=[...sec.matchAll(/<p class="citation-note fm-exposure-key">([\s\S]*?)<\/p>/g)].map(m=>visible(m[1]));
      for(const [i,track] of [[0,'sleep-scalp'],[1,'beta-8ch']]){
        const T=MVPJ.tracks.find(t=>t.id===track),best=T.rows.find(r=>r.id===C.vs_published_rows.find(x=>x.protocol===track).best_non_foundation.row);
        const ov=T.rows.filter(r=>r.id!==best.id&&r.family!=='foundation'&&r.interval[0]<=best.interval[1]&&best.interval[0]<=r.interval[1]);
        assert.ok(keys[i]&&keys[i].includes(zh?'点估计最高':'with the highest point estimate'),w+': '+track+' key names the reference row by its point estimate');
        if(ov.length) assert.ok(ov.every(r=>keys[i].includes(zh?`它的区间与 ${r.name} 的重叠`:`its interval overlaps ${r.name}’s`)),w+': '+track+' key says the reference row\'s interval overlaps '+ov.map(r=>r.name).join(', '));
        else assert.ok(!keys[i].includes(zh?'它的区间与':'its interval overlaps'),w+': '+track+' key claims an overlap the intervals do not have');
      }
      const aboveAll=matrix.filter(id=>relOf(id,'sleep-scalp').every(r=>r==='above'));
      assert.deepEqual(aboveAll,['reve-large','steegformer-base','steegformer-large'],'the handoff\'s sleep result: three encoders above every published row');
      const claim=sec.match(/<p class="roadmap-p" data-claim="sleep-above-all" data-models="([^"]+)">([\s\S]*?)<\/p>/);
      assert.ok(claim&&claim[1]===aboveAll.join(' '),w+': the sleep sentence names exactly the rows above all three published rows');
      for(const id of aboveAll) assert.ok(claim[2].includes('>'+e(name(id))+'<'),w+': the sleep sentence names '+name(id));
      assert.match(sec,zh?new RegExp(`睡眠分期：${aboveAll.length} 个新编码器高于所有已发布的行`):new RegExp(`Sleep staging: ${['zero','one','two','three','four'][aboveAll.length]} new encoders above every published row`),w+': the sleep heading counts them');
      // "above every published row": EEGNet's too, from the intervals; and sleep is the only protocol where any new row clears the best.
      for(const id of aboveAll) for(const r of MVPJ.tracks.find(t=>t.id==='sleep-scalp').rows) assert.ok(Number(cell('sleep-scalp',id).descriptive_interval_low_percent)>r.interval[1],w+': '+id+' lies above the released '+r.name+' sleep row');
      assert.equal(C.vs_published_rows.filter(x=>x.protocol!=='sleep-scalp'&&x.best_non_foundation.relation==='above').length,0,'no new row clears the best published row outside sleep');
      const pub=t=>[...sec.matchAll(new RegExp(`<span data-core-topic="${t}\\|([^"]+)">`,'g'))].map(m=>m[1]);
      assert.deepEqual([...new Set(pub('sleep-scalp'))],MVPJ.tracks.find(t=>t.id==='sleep-scalp').rows.map(r=>r.id),w+': every released sleep row, in the matrix order');
      assert.deepEqual([...new Set(pub('beta-8ch'))].sort(),MVPJ.tracks.find(t=>t.id==='beta-8ch').rows.map(r=>r.id).sort(),w+': every released BETA row');
      // BETA: the rows above CBraMod, the siblings above it too, none above standard CCA, the exposed cells below CBraMod.
      const b=sec.match(/data-claim="beta-above-cbramod" data-models="([^"]+)" data-ablation="([^"]+)"/);
      assert.ok(b&&b[1]===matrix.filter(id=>relOf(id,'beta-8ch')[1]==='above').join(' ')&&b[2]===siblings.filter(id=>relOf(id,'beta-8ch')[1]==='above').join(' '),w+': the BETA sentence names exactly the rows above CBraMod');
      assert.equal(b[2].split(' ').length,siblings.length,w+': "as do the three masking-ablation siblings"');
      assert.ok(C.vs_published_rows.filter(x=>x.protocol==='beta-8ch').every(x=>x.best_non_foundation.relation!=='above'&&x.best_non_foundation.row==='cca'),w+': no new BETA row above standard CCA');
      assert.ok(F.models.filter(m=>F.frozen_probe.find(x=>x.model===m.id&&x.protocol==='beta-8ch').exposure.status==='exposed').every(m=>m.id.startsWith('steegformer')&&relOf(m.id,'beta-8ch')[1]==='below'),w+': the exposed BETA cells are ST-EEGFormer\'s, below CBraMod');
      // EEGMAT: LaBraM for context, then the nine in the export's order, every figure, the verdict, the LoRA budgets.
      const A=F.eegmat_adaptation,ctx=A.published_context;
      const arows=[...sec.matchAll(/<tr data-adapt-row="([^"]+)"[^>]*>([\s\S]*?)<\/tr>/g)];
      assert.deepEqual(arows.map(m=>m[1]),['labram',...A.rows.map(r=>r.model)],w+': LaBraM for context, then the adapted encoders in the export\'s order');
      const lab=coreRow('arithmetic-rest','labram');
      for(const [,id,row] of arows){
        const r=id==='labram'?null:A.rows.find(x=>x.model===id),fr=r?r.arms['frozen-ce']:ctx.arms.frozen,lo=r?r.arms['lora-r4']:ctx.arms['lora-r4'],p=r?r.paired_lora_minus_frozen:ctx.paired_lora_minus_frozen;
        const ridge=r?[cell('arithmetic-rest',id).primary_percent,cell('arithmetic-rest',id).descriptive_interval_low_percent,cell('arithmetic-rest',id).descriptive_interval_high_percent].map(Number):[lab.y,...lab.interval];
        assert.deepEqual(rowFigs(row),[...ridge,fr.balanced_accuracy,...fr.interval_95,lo.balanced_accuracy,...lo.interval_95,p.mean_change,...p.interval_95,p.helped,p.harmed,p.tied,fr.trainable_parameters,lo.trainable_parameters],w+': EEGMAT '+id+': every arm, the change, people moved and both budgets');
        const zero=p.interval_95[0]>0||p.interval_95[1]<0;
        assert.ok(row.includes(`data-resolved="${zero}"`)&&row.includes(zh?(zero?'区间不含零。':'区间包含零：不能认定有变化。'):(zero?'The interval excludes zero.':'The interval includes zero: no change is established.')),w+': '+id+' carries the verdict its interval supports');
        if(r) assert.equal(zero,p.excludes_zero,w+': '+id+' the export\'s own flag');
        assert.equal(row.includes('data-exposure="unknown"'),id==='zuna',w+': '+id+' exposure unknown only for ZUNA 1.1');
      }
      const v=sec.match(/data-claim="adaptation-verdicts" data-models="([^"]+)" data-open="([^"]+)"/);
      assert.ok(v&&v[1]===A.rows.filter(r=>r.paired_lora_minus_frozen.excludes_zero).map(r=>r.model).join(' ')&&v[2]===A.rows.filter(r=>!r.paired_lora_minus_frozen.excludes_zero).map(r=>r.model).join(' '),w+': the verdict sentence names each side as the export does');
      assert.match(vis,zh?/不是排名/:/not a ranking/,w+': one fixed recipe on one task, not a ranking');
      assert.match(vis,zh?/LoRA 的参数量随架构而异/:/LoRA’s budget differs by architecture/,w+': LoRA budgets differ');
      for(const x of A.lora_parameter_range) assert.ok(sec.includes(`data-fig="${FMJ}|count|${x}"`),w+': the LoRA budget range '+x);
      const s1=A.rows.find(x=>x.model==='singlem'),sc=cell('arithmetic-rest','singlem');
      assert.ok(Number(sc.interval_includes_chance==='true')&&s1.arms['frozen-ce'].interval_95[0]<=A.chance_level&&s1.arms['lora-r4'].interval_95[0]>A.chance_level&&s1.paired_lora_minus_frozen.excludes_zero,w+': the SingLEM sentence: frozen readouts reach chance, LoRA does not');
      const na=sec.match(/data-claim="not-adapted">([\s\S]*?)<\/p>/)[1];
      for(const m of F.models.filter(m=>m.adaptation!=='run')) assert.ok(na.includes('>'+e(m.name)+'<')&&na.includes(e(zh?Z[m.adaptation]:(EN_SHOWN[m.adaptation]??m.adaptation))),w+': '+m.name+' not adapted, with the export\'s reason');
      // REVE Base and Large: every scored protocol, both rows, the export's change and overlap; the pattern and its caveat.
      const pairs=C.base_vs_large.filter(x=>x.base==='reve-base');
      const srows=[...sec.matchAll(/<tr data-size-pair="([^"]+)" data-overlap="(true|false)">([\s\S]*?)<\/tr>/g)];
      assert.deepEqual(srows.map(m=>m[1]),scored,w+': REVE on every scored protocol, in the matrix order');
      for(const [,t,ov,row] of srows){
        const x=pairs.find(p=>p.protocol===t),bc=cell(t,'reve-base'),lc=cell(t,'reve-large');
        assert.equal(ov,String(x.marginal_intervals_overlap),w+': REVE '+t+' overlap is the export\'s');
        assert.ok(row.includes(x.marginal_intervals_overlap?(zh?'>重叠<':'>Overlap<'):(zh?'<strong class="fm-sep">不重叠</strong>':'<strong class="fm-sep">Do not overlap</strong>')),w+': REVE '+t+' says so');
        assert.deepEqual(rowFigs(row).slice(1),[bc.primary_percent,bc.descriptive_interval_low_percent,bc.descriptive_interval_high_percent,lc.primary_percent,lc.descriptive_interval_low_percent,lc.descriptive_interval_high_percent].map(Number).concat(x.large_minus_base),w+': REVE '+t+': both rows and the export\'s change');
      }
      assert.ok(pairs.every(p=>p.large_minus_base>=0),'REVE Large is at or above Base everywhere');
      assert.ok(sec.includes(`data-claim="reve-separated" data-tracks="${pairs.filter(p=>!p.marginal_intervals_overlap).map(p=>p.protocol).join(' ')}"`),w+': the size sentence names where the intervals separate');
      // Follow-up review of 2026-10-05: on the protocols where the intervals overlap, "at or above" orders point estimates.
      assert.ok(vis.includes(zh?'REVE Large 的点估计都不低于 REVE Base':'REVE Large’s point estimate is at or above REVE Base’s')&&!/REVE Large is at or above|REVE Large 都不低于/.test(vis),w+': REVE Large against Base as point estimates');
      assert.match(vis,zh?/没有做配对检验/:/no paired test was run/,w+': no paired test');
      assert.match(vis,zh?/边际区间/:/marginal/,w+': marginal intervals');
      assert.match(vis,zh?/同一批被试/:/the same people/,w+': the same people');
      const o=sec.match(/data-claim="other-size-pairs" data-luna="([^"]*)" data-st="([^"]*)"/);
      assert.ok(o&&o[1]===C.base_vs_large.filter(x=>x.base==='luna-base'&&!x.marginal_intervals_overlap).map(x=>x.protocol).join(' ')&&o[2]===C.base_vs_large.filter(x=>x.base==='steegformer-base'&&!x.marginal_intervals_overlap).map(x=>x.protocol).join(' '),w+': the other size pairs, where the export says they separate');
      assert.ok(o[2].split(' ').every(t=>F.frozen_probe.find(x=>x.model==='steegformer-base'&&x.protocol===t).exposure.status==='exposed'),'ST-EEGFormer separates only on exposed cells');
      // Masking: four checkpoints on every scored protocol; the separated pairs; six of seven.
      const mrows=[...sec.matchAll(/<tr data-masking="([^"]+)" data-separated="([^"]+)">([\s\S]*?)<\/tr>/g)];
      assert.deepEqual(mrows.map(m=>m[1]),scored,w+': the masking ablation on every scored protocol');
      for(const [,t,sep,row] of mrows){
        const x=C.masking_ablation.find(m=>m.protocol===t);
        assert.equal(sep,x.non_overlapping_pairs.map(p=>p.join('+')).join(' ')||'none',w+': masking '+t+' separated pairs are the export\'s');
        assert.deepEqual([...row.matchAll(/data-fm-topic="[^|]+\|([^"]+)"/g)].map(m=>m[1]),F.masking_ablation.checkpoints,w+': masking '+t+' the four checkpoints in order');
        assert.deepEqual(rowFigs(row),F.masking_ablation.checkpoints.flatMap(id=>{const c=cell(t,id);return [c.primary_percent,c.descriptive_interval_low_percent,c.descriptive_interval_high_percent].map(Number);}),w+': masking '+t+' every cell');
        assert.equal(row.includes(zh?'没有：两两都重叠':'None: every pair overlaps'),!x.non_overlapping_pairs.length,w+': masking '+t+' says whether a pair separates');
        for(const [p1,p2] of x.non_overlapping_pairs) assert.ok(/jepa/.test(p1)!==/jepa/.test(p2)&&/r9cm/.test(p1)!==/r9cm/.test(p2),'the separated masking pair changes both factors');
      }
      const insep=C.masking_ablation.filter(m=>!m.non_overlapping_pairs.length).length;
      // The two full tables sit in collapsed panels; the sentences above them carry the readings.
      for(const id of ['v9-size-table','v9-masking-table']) assert.ok(sec.includes(`<details class="rd-panel fm-panel" id="${id}">`),w+': #'+id+' is a collapsed panel');
      assert.match(sec,zh?new RegExp(`掩码消融：${scored.length} 个协议中有 ${insep} 个分不出差别`):new RegExp(`Masking ablation: not separable on ${['zero','one','two','three','four','five','six','seven'][insep]} of ${['zero','one','two','three','four','five','six','seven'][scored.length]} protocols`),w+': the masking heading counts the protocols');
      assert.match(vis,zh?/同时改变了掩码框架和掩码几何/:/changes the framework and the geometry at once/,w+': the separated pair changes both factors');
      // Limits: each of the export's required limitations, in the page's words; exposure as the owner's statement.
      const lim=sec.slice(sec.indexOf('id="v9-limits"'),sec.indexOf('id="v9-licences"'));
      for(const re of zh?[/不是上限/,/未调参、训练 5 轮/,/没有计入交叉验证带来的相关性/,/多重比较校正/,/从不排名/,/不是实际使用中检出率、误报率或延迟的估计/,/没有跨天、跨设备或跨数据集的证据/,/临床/,/1–2 秒时间窗/,/ZUNA 1\.1 没有公开清单/,/EEGMamba 的清单读自其官方代码，把握程度为中等/,/作者都没有为这些结果背书/,/LoRA 增量/,/共享 GPU/]
                       :[/not a ceiling/,/untuned five-epoch recipe/,/ignore cross-validation dependence/,/no multiplicity correction/,/Grouped, never ranked/,/not detection, false-alarm or latency estimates for real use/,/cross-day, cross-device or cross-dataset/,/clinical claim/,/1–2 s windows/,/ZUNA 1\.1 publishes none/,/EEGMamba’s list is read from its official code, with medium confidence/,/No model’s authors endorse these results/,/LoRA deltas/,/shared GPU/])
        assert.match(visible(lim),re,w+': the limitation '+re);
      for(const k of ['mi-rest','p300-target','sleep-scalp']) assert.ok(lim.includes(`data-fig="${FMJ}|count|${F.protocols.find(p=>p.id===k).people}"`),w+': the small cohort of '+k);
      // Licences: one entry per family printed, with its weights licence, note and paper.
      const lic=sec.slice(sec.indexOf('<ul class="entity-links protocol-prose fm-licences">'),sec.indexOf('</ul>',sec.indexOf('fm-licences')));
      const fams=[...new Set(F.models.map(m=>m.id).map(id=>({'reve-base':'reve','reve-large':'reve','luna-base':'luna','luna-large':'luna','brainomni-base':'brainomni','steegformer-base':'st-eegformer','steegformer-large':'st-eegformer','erp-fm-base':'erp-fm'})[id]??(id.startsWith('eeg-fm-masking/')?'eeg-fm-masking':id)))];
      assert.deepEqual([...lic.matchAll(/<li data-licence="([^"]+)">/g)].map(m=>m[1]),fams,w+': one licence entry per family, in the export\'s order');
      for(const f of fams){
        const m=F.models.find(x=>(({'reve-base':'reve','reve-large':'reve','luna-base':'luna','luna-large':'luna','brainomni-base':'brainomni','steegformer-base':'st-eegformer','steegformer-large':'st-eegformer','erp-fm-base':'erp-fm'})[x.id]??(x.id.startsWith('eeg-fm-masking/')?'eeg-fm-masking':x.id))===f);
        const li=lic.slice(lic.indexOf(`<li data-licence="${f}">`),lic.indexOf('</li>',lic.indexOf(`<li data-licence="${f}">`)));
        assert.ok(li.includes(e(zh?Z[m.weights_licence]:m.weights_licence))&&li.includes(`href="${m.paper}"`),w+': '+f+' weights licence and paper');
        if(m.licence_note.replace(/\.$/,'')!==m.weights_licence) assert.ok(li.includes(e(zh?Z[m.licence_note]:m.licence_note)),w+': '+f+' licence note');
      }
      assert.ok(lic.slice(lic.indexOf('<li data-licence="reve">'),lic.indexOf('</li>',lic.indexOf('<li data-licence="reve">'))).includes(reveVersions),w+': the REVE licence entry names the model versions');
      assert.ok(sec.includes(`href="/${prefix}releases/#${REL}"`),w+': the release is linked');
    }

    // --- fewer-electrodes #v9-montage ---
    {
      const {html,sec,vis,figs,w}=common(prefix+'topics/fewer-electrodes/','v9-montage');
      xsec[label+'M']=figs.map(f=>f.file+'|'+f.raw);
      const pos=html.indexOf('id="v9-montage"');
      assert.ok(pos>html.indexOf('id="posterior-subset"')&&pos<html.indexOf('id="methods-and-limits"'),w+': after the two paired comparisons, before their methods and limits');
      const rows=[...sec.matchAll(/<tr data-montage-row="([^"]+)" data-released="(true|false)" data-overlap="(true|false)"(?: data-input="([^"]+)")?>([\s\S]*?)<\/tr>/g)];
      const released=rows.filter(r=>r[2]==='true'),fresh=rows.filter(r=>r[2]==='false');
      const b8=MVPJ.tracks.find(t=>t.id==='beta-8ch'),b4=MVPJ.tracks.find(t=>t.id==='beta-4ch'),sl=MVPJ.tracks.find(t=>t.id==='sleep-scalp');
      assert.deepEqual(released.map(r=>r[1]),b8.rows.map(r=>r.id),w+': every released BETA row, in the matrix order');
      for(const [,id,,ov,,row] of released){
        const r8=b8.rows.find(r=>r.id===id),r4=b4.rows.find(r=>r.id===id),rs=sl.rows.find(r=>r.id===id);
        assert.equal(ov,String(r8.interval[0]<=r4.interval[1]&&r4.interval[0]<=r8.interval[1]),w+': released '+id+': whether its two intervals overlap');
        assert.deepEqual(rowFigs(row),[r8.y,...r8.interval,r4.y,...r4.interval,...(rs?[rs.y,...rs.interval]:[])],w+': released '+id+': its rows as released');
        assert.ok(!/ pp</.test(row),w+': released '+id+': no difference no released file states');
        if(!rs) assert.match(row,zh?/不在睡眠协议中/:/Not in the sleep protocol/,w+': '+id+' is not in the sleep protocol, and says so');
      }
      assert.deepEqual(fresh.map(r=>r[1]),matrix,w+': every new matrix row, in the export\'s order');
      for(const [,id,,ov,inp,row] of fresh){
        const x=C.fewer_electrodes_beta.find(c=>c.model===id),c8=cell('beta-8ch',id),c4=cell('beta-4ch',id),cs=cell('sleep-scalp',id);
        assert.equal(ov,String(x.marginal_intervals_overlap),w+': '+id+': the export\'s overlap');
        assert.equal(inp,x.input_family,w+': '+id+': its input family');
        assert.deepEqual(rowFigs(row),[...[c8,c4].flatMap(c=>[c.primary_percent,c.descriptive_interval_low_percent,c.descriptive_interval_high_percent].map(Number)),x.four_minus_eight,...[cs.primary_percent,cs.descriptive_interval_low_percent,cs.descriptive_interval_high_percent].map(Number)],w+': '+id+': both montages, the export\'s change and sleep');
        assert.ok(row.includes(x.marginal_intervals_overlap?(zh?'区间重叠':'Intervals overlap'):(zh?'区间不重叠':'Intervals do not overlap')),w+': '+id+' says whether its intervals overlap');
      }
      // The two readings: no small-montage advantage for the non-montage encoders; standard CCA keeps the highest four-electrode score.
      const non=C.fewer_electrodes_beta.filter(x=>x.input_family!=='montage'&&matrix.includes(x.model));
      assert.deepEqual(non.map(x=>x.model).sort(),['singlem','zuna'],'the single-channel and channel-wise encoders');
      assert.ok(non.every(x=>x.four_minus_eight<0&&!x.marginal_intervals_overlap),w+': both lost accuracy at four electrodes, intervals apart');
      const n=sec.match(/data-claim="no-small-montage-advantage" data-models="([^"]+)">([\s\S]*?)<\/p>/);
      const above=C.fewer_electrodes_beta.filter(x=>x.input_family==='montage'&&matrix.includes(x.model)&&relOf(x.model,'beta-8ch')[1]==='above'&&relOf(x.model,'beta-4ch')[1]==='above').map(x=>x.model);
      assert.ok(n&&n[1]===above.join(' '),w+': the montage encoders above CBraMod at both montages');
      for(const x of [...non,...C.fewer_electrodes_beta.filter(c=>above.includes(c.model))]) assert.ok(n[2].includes(`data-fig="${FMJ}|pp1|${x.four_minus_eight}"`),w+': the change of '+x.model);
      const sg=Number(cell('sleep-scalp','singlem').descriptive_interval_high_percent);
      assert.ok(matrix.filter(id=>id!=='singlem').every(id=>sg<Number(cell('sleep-scalp',id).descriptive_interval_low_percent))&&sl.rows.every(r=>sg<r.interval[0]),w+': SingLEM lies below every other sleep row');
      assert.match(vis,zh?/没有优势/:/No small-montage advantage/,w+': no small-montage advantage');
      // The short answer says the new encoders as a whole show none: no new row is higher at four electrodes with intervals apart.
      assert.ok(C.fewer_electrodes_beta.filter(x=>matrix.includes(x.model)).every(x=>x.four_minus_eight<=0||x.marginal_intervals_overlap),'no new row gains at four electrodes with intervals apart');
      // Standard CCA at four electrodes, as interval facts (review of 2026-10-05): no new row above it; the new rows and the
      // released rows whose intervals overlap it named, the released ones with their figures. Never "keeps the highest score".
      const cc=b4.rows.find(r=>r.id==='cca');
      const cl=sec.match(/data-claim="cca-four-electrodes" data-models="([^"]+)" data-released="([^"]+)">([\s\S]*?)<\/p>/);
      assert.ok(cl&&cl[1]===matrix.filter(id=>relOf(id,'beta-4ch')[2]==='overlap').join(' ')&&matrix.every(id=>relOf(id,'beta-4ch')[2]!=='above'),w+': no new row above CCA; the overlapping ones named');
      const relOverlap=b4.rows.filter(r=>r.id!=='cca'&&r.interval[0]<=cc.interval[1]&&cc.interval[0]<=r.interval[1]);
      assert.ok(relOverlap.length&&cl[2]===relOverlap.map(r=>r.id).join(' '),w+': the released rows whose four-electrode interval overlaps CCA\'s are named');
      for(const r of relOverlap) assert.ok([r.y,...r.interval].every(v=>cl[3].includes(`data-fig="experiments.json|pct1raw|${v}"`))&&cl[3].includes(`data-core-topic="beta-4ch|${r.id}"`),w+': '+r.id+' printed with its four-electrode interval');
      assert.match(sec,zh?/<h3 class="roadmap-h3" id="v9-cca">在 4 个电极上，没有任何新编码器高于标准 CCA<\/h3>/:/<h3 class="roadmap-h3" id="v9-cca">No new encoder lies above standard CCA at four electrodes<\/h3>/,w+': the CCA heading states an interval fact');
      // The short answer (and so FAQPage) says the same, without the ranking.
      const ans=visible(html.slice(html.indexOf('<section class="short-answer"'),html.indexOf('</section>',html.indexOf('<section class="short-answer"'))));
      assert.ok(ans.includes(zh?'在 4 个电极上，也没有任何新编码器高于免训练的标准 CCA':'no new encoder lies above training-free CCA at four electrodes')&&!/keeps the highest|仍是 4 个电极上的最高分|最高分/.test(ans),w+': the short answer states the CCA reading as an interval fact');
      for(const re of zh?[/不能验证一顶实体的少通道电极帽/,/接近下限的分数在两个子集之间的先后并不可靠/,/不是上面的 EESM23，也不是耳部 EEG/,/两个睡眠结果不能放进同一个排名/,/没有做配对检验/]
                       :[/does not validate a physical low-channel cap/,/near-floor scores are not ordered reliably/,/not EESM23 above and not ear-EEG/,/do not share a ranking/,/no paired test/])
        assert.match(vis,re,w+': '+re);
      // The v9 export's required limitations that does-pretraining-help carries, in this page's words (review of 2026-10-05):
      // small cohorts with descriptive intervals and no multiplicity correction, balanced designs as method comparisons,
      // new people on the same task and setup only, windows shorter than the pretraining contexts.
      const lim=sec.slice(sec.indexOf('<div class="method-grid-wide fm-limits">'),sec.indexOf('</div>',sec.indexOf('<div class="method-grid-wide fm-limits">')));
      for(const re of zh?[/小队列，描述性区间/,/没有计入交叉验证带来的相关性/,/没有做多重比较校正/,/冻结单元格共有 126 个，偶尔出现不重叠，本身就在随机误差的预料之中/,/不是实际使用中检出率、误报率或延迟的估计/,/没有跨天、跨设备或跨数据集的证据/,/临床/,/1–2 秒时间窗/,/通常比它预训练时的上下文更短/,/EEGMamba 的清单读自其官方代码（论文全文没有读过），把握程度为中等/]
                       :[/Small cohorts, descriptive intervals/,/ignores cross-validation dependence/,/no multiplicity correction/,/with 126 frozen cells an occasional non-overlap is expected by chance/,/not detection, false-alarm or latency estimates for real use/,/cross-day, cross-device or cross-dataset/,/clinical claim/,/1–2 s windows/,/shorter than its pretraining context/,/EEGMamba’s list is read from its official code \(its paper was not read\), with medium confidence/])
        assert.match(visible(lim),re,w+': the limitation '+re);
      for(const k of ['beta-8ch','sleep-scalp']) assert.ok(lim.includes(`data-fig="${FMJ}|count|${F.protocols.find(p=>p.id===k).people}"`),w+': the small cohort of '+k);
      // Licence notes travel with the rows: one entry per family printed, REVE by version, no endorsement.
      const lic=sec.slice(sec.indexOf('<ul class="entity-links protocol-prose fm-licences">'),sec.indexOf('</ul>',sec.indexOf('fm-licences')));
      const fams=[...new Set(matrix.map(famOf))];
      assert.deepEqual([...lic.matchAll(/<li data-licence="([^"]+)">/g)].map(m=>m[1]),fams,w+': one licence entry per family printed, in the export\'s order');
      for(const f of fams){
        const m=F.models.find(x=>famOf(x.id)===f),li=lic.slice(lic.indexOf(`<li data-licence="${f}">`),lic.indexOf('</li>',lic.indexOf(`<li data-licence="${f}">`)));
        assert.ok(li.includes(e(zh?Z[m.weights_licence]:m.weights_licence))&&li.includes(`href="${m.paper}"`),w+': '+f+' weights licence and paper');
        if(m.licence_note.replace(/\.$/,'')!==m.weights_licence) assert.ok(li.includes(e(zh?Z[m.licence_note]:m.licence_note)),w+': '+f+' licence note');
      }
      assert.ok(lic.slice(lic.indexOf('<li data-licence="reve">'),lic.indexOf('</li>',lic.indexOf('<li data-licence="reve">'))).includes(reveVersions),w+': the REVE licence entry names the model versions');
      assert.ok(sec.includes('<p class="protocol-note fm-no-endorsement">'+(zh?'任何模型的作者都没有为这些结果背书':'No model’s authors endorse these results')),w+': no author endorses these results');
    }
    // model-adaptation: a pointer to the table, no figure; its own claims are pinned above.
    {
      const html=pageOf(prefix+'topics/model-adaptation/'),a=html.indexOf('<p class="protocol-note" id="v9-pointer">'),ptr=html.slice(a,html.indexOf('</p>',a));
      assert.ok(a>html.indexOf('id="adaptation"')&&a<html.indexOf('id="next-day"'),prefix+'topics/model-adaptation/: the pointer sits in #adaptation');
      assert.ok(ptr.includes(`href="/${prefix}topics/does-pretraining-help/#v9-adaptation"`)&&pageOf(prefix+'topics/does-pretraining-help/').includes('id="v9-adaptation"'),prefix+'topics/model-adaptation/: the pointer lands on the v9 adaptation');
      assert.doesNotMatch(visible(ptr),/\d+\.\d|%|\bpp\b|data-fig/,prefix+'topics/model-adaptation/: the pointer carries no figure');
      assert.match(visible(ptr),zh?/不是排名/:/not a ranking/,prefix+'topics/model-adaptation/: the pointer says the table is not a ranking');
    }
  }
  assert.deepEqual(xsec.zhP,xsec.enP,'does-pretraining-help #v9-encoders: the same figures in both languages, in order');
  assert.deepEqual(xsec.zhM,xsec.enM,'fewer-electrodes #v9-montage: the same figures in both languages, in order');
  // The release log names both topics; the transfer map's two entries are pinned with the other map pins above.
  for(const prefix of ['','zh/']){
    const rel=pageOf(prefix+'releases/'),entry=rel.slice(rel.indexOf(`id="${REL}"`),rel.indexOf('</article>',rel.indexOf(`id="${REL}"`)));
    for(const t of ['does-pretraining-help','fewer-electrodes']) assert.ok(entry.includes(`href="/${prefix}topics/${t}/"`),prefix+'releases/: the v9 release names '+t);
    // Interval facts and the authors' lists, never a ranking or a corpus claim (review of 2026-10-05).
    assert.doesNotMatch(visible(entry),/stays? the highest|best published non-foundation|was pretrained on|仍是最高|最佳非基础模型行|的预训练数据包含/,prefix+'releases/: the v9 note ranks no overlapping rows and claims no corpus');
    assert.ok(visible(entry).includes(prefix?'没有任何新行高于无需训练的标准 CCA':'no new row lies above standard CCA, which needs no training'),prefix+'releases/: the v9 note says no new row lies above standard CCA');
    if(!prefix){const feed=readFileSync(new URL('releases.xml',DIST),'utf8'),fe=feed.slice(feed.indexOf(`<id>https://bci.report/releases/#${REL}</id>`),feed.indexOf('</entry>',feed.indexOf(`#${REL}</id>`)));
      assert.ok(fe.length>500&&!/stays? the highest|best published non-foundation|was pretrained on/.test(fe),'releases.xml: the v9 entry ranks no overlapping rows and claims no corpus');}
  }
  // The Questions hub changed again on 2026-10-07 (route 2's card) and 2026-10-08 (the later-sessions card), and
  // does-pretraining-help on 2026-10-08 (its pointer to the later-sessions question), so they carry that date now.
  for(const p of ['topics/fewer-electrodes/','topics/does-pretraining-help/','topics/model-adaptation/','topics/']){
    const d=p==='topics/'||p==='topics/does-pretraining-help/'?'2026-10-08':'2026-10-04';
    assert.ok(sitemap.includes(`<loc>https://bci.report/${p}</loc><lastmod>${d}</lastmod>`),'sitemap: '+p+' changed on '+d);}
}
// --- 2026-10-05 review: the Markdown copies of the route-1 and v9 sections ---------------------------
// The generic copy check above only looks for figures in elements whose class is exactly metric, num or fig, and
// accepts them anywhere in the copy; most interval bounds and coverages in these sections are neither, and
// llms-full.txt is assembled from the copies. Here, for each route-1 and v9 section and entity group, the printed
// data-fig texts, in order, must be an ordered subsequence of the matching section of its index.md (found by its
// heading, ending at the next heading of the same level), each occurrence bounded as a number, and each text at
// least as often as the page prints it; and every English copy in llms-full.txt is the copy itself, verbatim.
{
  const norm=t=>decodeHtml(t).replace(/\[([^\]]*)\]\([^)]*\)/g,'$1').replace(/\*\*|`/g,'').replace(/\s+/g,' ').replace(/\s+([,.;:)])/g,'$1').replace(/\(\s+/g,'(').trim();
  const sectionHtml=(html,id)=>{const a=html.search(new RegExp(`<section\\b[^>]*\\sid="${id}"`));if(a<0)return null;
    const re=/<section\b|<\/section>/g;re.lastIndex=a;let d=0,m;while((m=re.exec(html))){d+=m[0]==='</section>'?-1:1;if(!d)return html.slice(a,m.index);}return null;};
  const figTexts=h=>[...h.matchAll(/data-fig="[^"]+"[^>]*>([^<]*)</g)].map(m=>decodeHtml(m[1]));
  const esc=t=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const bounded=t=>new RegExp(`(?<![\\d.,])${esc(t)}(?!\\d|[.,]\\d)`,'g');
  const mdSection=(md,head,level)=>{const lines=md.split('\n');const i=lines.findIndex(l=>new RegExp(`^#{${level}} `).test(l)&&norm(l.replace(/^#+ /,''))===head);
    if(i<0)return null;let j=i+1;while(j<lines.length&&!new RegExp(`^#{1,${level}} `).test(lines[j]))j++;return lines.slice(i,j).join('\n');};
  let checked=0;
  const copyCarries=(path,id,where)=>{
    const html=readFileSync(new URL(path+'index.html',DIST),'utf8'),md=readFileSync(new URL(path+'index.md',DIST),'utf8');
    const sec=sectionHtml(html,id);assert.ok(sec,where+': section #'+id+' renders');
    const h=sec.match(/<h([23])\b[^>]*>([\s\S]*?)<\/h\1>/);assert.ok(h,where+': #'+id+' has a heading');
    const head=norm(h[2].replace(/<[^>]+>/g,' ')),part=mdSection(md,head,Number(h[1]));
    assert.ok(part,where+': the copy has the section "'+head.slice(0,60)+'"');
    const figs=figTexts(sec);assert.ok(figs.length>0,where+': #'+id+' prints figures');
    let pos=0;
    for(const t of figs){const re=bounded(t);re.lastIndex=pos;const m=re.exec(part);
      assert.ok(m,where+': index.md #'+id+' lacks "'+t+'" after its preceding figures (in order)');pos=m.index+t.length;}
    // As often as the page prints it, counting its text outside data-fig too (a plot's value list repeats a table's
    // figures, so an order match alone could land on the plot and miss a changed table cell).
    // What the copy leaves out on purpose: SVG, anything aria-hidden, visually hidden labels (build-agent-files.mjs).
    const shown=decodeHtml(sec.replace(/<svg[\s\S]*?<\/svg>/g,' ').replace(/<(\w+)[^>]*aria-hidden="true"[^>]*>[\s\S]*?<\/\1>/g,' ')
      .replace(/<span class="visually-hidden">[^<]*<\/span>/g,' ').replace(/<[^>]+>/g,' '));
    // Bare whole numbers (10, 70) are left to the order check: dates and section labels repeat them in prose.
    for(const t of new Set(figs.filter(t=>/[.%,]/.test(t)))){const n=(shown.match(bounded(t))||[]).length;
      assert.ok((part.match(bounded(t))||[]).length>=n,where+': index.md #'+id+' prints "'+t+'" fewer times than the page ('+n+')');}
    checked+=figs.length;
  };
  for(const pfx of ['','zh/']){
    copyCarries(pfx+'topics/when-not-to-act/','reliable-decisions',pfx+'when-not-to-act');
    copyCarries(pfx+'topics/does-pretraining-help/','v9-encoders',pfx+'does-pretraining-help');
    copyCarries(pfx+'topics/fewer-electrodes/','v9-montage',pfx+'fewer-electrodes');
    for(const t of data.tracks) copyCarries(pfx+'protocols/'+t.id+'/','foundation-v9',pfx+'protocols/'+t.id);
    // Route 2 (2026-10-07): every section of its question that prints a figure.
    for(const id of ['motor-imagery','sleep','eesm19','secondary','methods-and-limits']) copyCarries(pfx+'topics/shared-encoder/',id,pfx+'shared-encoder');
    // Every route-1, v9 and route-2 group on the dataset and method pages.
    for(const f of htmlPages.filter(f=>f.startsWith(pfx+'datasets/')||f.startsWith(pfx+'methods/')).filter(f=>pfx||!f.startsWith('zh/'))){
      const html=readFileSync(new URL(f,DIST),'utf8'),path=f.replace(/index\.html$/,'');
      for(const [,gid] of html.matchAll(/<section class="entity-group" id="(g-[^"]*(?:reliable-decisions|foundation-v9|v9-adaptation|shared-encoder))"(?: data-boas="true")?>/g))
        if(sectionHtml(html,gid).includes('data-fig')) copyCarries(path,gid,path+' '+gid);
    }
  }
  assert.ok(checked>3000,'the route-1 and v9 copy check read the sections ('+checked+' figures)');
  // llms-full.txt is assembled from the English copies: each one is in it, verbatim.
  const full=readFileSync(new URL('llms-full.txt',DIST),'utf8');
  for(const f of htmlPages.filter(f=>!f.startsWith('zh/')&&f!=='404.html'&&/^(?:index\.html|(?:topics|datasets|methods|protocols)\/(?:[^/]+\/)?index\.html|(?:api|releases|data-use)\/index\.html)$/.test(f))){
    const md=readFileSync(new URL(f.replace(/index\.html$/,'index.md'),DIST),'utf8').trim();
    assert.ok(full.includes(md),'llms-full.txt: the copy of /'+f.replace(/index\.html$/,'')+' is in it, verbatim');
  }
  // Follow-up review of 2026-10-05: two places on this branch still reached the copies unchecked. (1) The home page's
  // per-protocol table, its v9 group and masking-ablation rows: the first paint's figures, row by row and in order, must
  // be the figures of the same rows of index.md's table (the v9 rows after the released ones, the ablation panel's own
  // table), so llms-full.txt (verbatim, above) carries them too. (2) Every topic page's short answer: the bold figures
  // of the copy's short answer are the [[…]]-marked figures of the page's, in order.
  const figTokens=t=>[...decodeHtml(t).matchAll(/\d[\d,]*\.\d+%?|\d+%/g)].map(m=>m[0]);
  let homeRows=0,answers=0;
  for(const pfx of ['','zh/']){
    const html=readFileSync(new URL(pfx+'index.html',DIST),'utf8'),md=readFileSync(new URL(pfx+'index.md',DIST),'utf8');
    const tbody=id=>{const a=html.indexOf(`<tbody id="${id}"`);assert.ok(a>0,pfx+'index.html: #'+id);return html.slice(a,html.indexOf('</tbody>',a));};
    const rowsOf=b=>[...b.matchAll(/<tr class="fm-row" data-fm="[^"]+">([\s\S]*?)<\/tr>/g)].map(m=>({name:decodeHtml(m[1].match(/<button[^>]*>([^<]*)<\/button>/)[1]).replace(/ ↗$/,''),figs:figTokens(m[1].replace(/<[^>]+>/g,' '))}));
    const tables=md.split('\n\n').filter(b=>b.trimStart().startsWith('|')).map(b=>b.split('\n').filter(l=>l.startsWith('|')&&!/^\|\s*---/.test(l)));
    const mdRow=(table,name)=>table.filter(l=>l.startsWith('| '+name+' — '));
    for(const [id,pick,label] of [['result-rows',ts=>ts.find(t=>t.some(l=>/\| (?:\d+ further foundation encoders, frozen|另外 \d+ 个基础模型编码器（冻结）)/.test(l))),'v9 group'],
                                  ['ablation-rows',ts=>ts.find(t=>t.some(l=>/— (?:matrix row above|即上方的矩阵行)/.test(l))||(t.length===4&&t.every(l=>/^\| eeg-fm-masking /.test(l)))),'masking ablation']]){
      const rows=rowsOf(tbody(id)),table=pick(tables),where=pfx+'index.md, the home '+label;
      assert.ok(rows.length>0&&table,where+': the page\'s rows and the copy\'s table');
      const names=table.map(l=>l.slice(2).split(' — ')[0]).filter(n=>rows.some(r=>r.name===n));
      assert.deepEqual(names,rows.map(r=>r.name),where+': the same rows, in the same order');
      for(const r of rows){const m=mdRow(table,r.name);
        assert.ok(m.length===1,where+': one row for '+r.name);
        assert.deepEqual(figTokens(m[0]),r.figs,where+': '+r.name+' carries the page\'s figures, in order');homeRows++;}
    }
  }
  assert.ok(homeRows>=2*(13+4),'the home v9 and ablation rows were read ('+homeRows+')');
  for(const [slug] of topicPages) for(const pfx of ['','zh/']){
    const html=readFileSync(new URL(pfx+'topics/'+slug+'/index.html',DIST),'utf8'),md=readFileSync(new URL(pfx+'topics/'+slug+'/index.md',DIST),'utf8');
    const a=html.indexOf('<section class="short-answer"'),sec=html.slice(a,html.indexOf('</section>',a));
    const head=decodeHtml(sec.match(/<h2 id="short-answer-heading">([^<]*)<\/h2>/)[1]),page=[...sec.matchAll(/<strong class="fig">([^<]*)<\/strong>/g)].map(m=>decodeHtml(m[1]));
    const part=mdSection(md,head,2),where=pfx+'topics/'+slug+'/index.md';
    assert.ok(part,where+': the copy has the short answer');
    // The answer is the first paragraph under its heading; what follows it before the next heading is the evidence.
    const para=part.split('\n').slice(1).join('\n').trim().split('\n\n')[0];
    assert.deepEqual([...para.matchAll(/\*\*([^*]+)\*\*/g)].map(m=>m[1]),page,where+': the short answer\'s bold figures are the page\'s marked figures, in order');
    answers++;
  }
  // No space before a full-width mark in a Chinese copy (the converter spaces two adjacent elements, so a closing
  // bracket that opens the next element read "（−6.1 pp ）" on fewer-electrodes).
  for(const f of htmlPages.filter(f=>f.startsWith('zh/'))){const md=readFileSync(new URL(f.replace(/index\.html$/,'index.md'),DIST),'utf8');
    const bad=md.match(/.{0,20}[^\s|] [）；，。：、].{0,4}/);assert.ok(!bad,f.replace(/index\.html$/,'index.md')+': a space before a full-width mark: "'+(bad&&bad[0])+'"');}
  // Second follow-up review of 2026-10-05: the checks above read data-fig texts, home rows and short answers, so v9
  // figures written as plain text still reached the copies (and, verbatim, llms-full.txt) with nothing holding them.
  const squash=t=>norm(t).replace(/\s+/g,'');
  // What the converter (build-agent-files.mjs) leaves out of a block: SVG, aria-hidden, visually hidden labels, form
  // controls and in-page jump links.
  const blockText=h=>h.replace(/<svg[\s\S]*?<\/svg>/g,' ').replace(/<(\w+)[^>]*aria-hidden="true"[^>]*>[\s\S]*?<\/\1>/g,' ')
    .replace(/<span class="visually-hidden">[^<]*<\/span>/g,' ').replace(/<(button|select|label)\b[\s\S]*?<\/\1>/g,' ')
    .replace(/<a href="#[^"]*"[^>]*>[\s\S]*?<\/a>/g,' ').replace(/<[^>]+>/g,' ');
  const FMX=JSON.parse(readFileSync(new URL('data/foundation-models-update.json',DIST),'utf8')).results['foundation-models-v9'];
  const RDX=JSON.parse(readFileSync(new URL('data/reliable-decisions-update.json',DIST),'utf8')).results['reliable-decisions'];
  const ZT=(()=>{const c={};vm.runInNewContext(stripTypeScriptTypes(readFileSync(new URL('../src/data/foundation-models-zh.ts',import.meta.url),'utf8'))
    .replace(/^import[^\n]*\n/gm,'').replace(/^export /gm,'')+'\nthis.fmZh=fmZh;',c);return c.fmZh;})();
  const inLang=(en,zh)=>zh?{text:ZT[en],original:en}:{text:en};
  // A copy's list item, "- " and any label first; a Chinese text and its English are two elements on a protocol page
  // (a space between them) and a text and an element in a checkpoint's term (none).
  const itemIs=(line,lead,t)=>!!t.text&&(t.original?[lead+t.text+' '+t.original,lead+t.text+t.original].includes(line):line===lead+t.text);
  // (N3a) REVE's row footnotes state the sensitivity run's size and direction in words ("P300 0.71 percentage points
  // higher and sleep 1.40 lower"), inside a list item the data-fig check cannot see: a sign reversed in a copy and in
  // llms-full.txt passed. Every row footnote a page prints — each protocol page's numbered list, each checkpoint on a
  // method page — is in its copy verbatim, in the page's order: in English the export's row_footnote, in Chinese the
  // translation table's text followed by the English (llms-full.txt, held verbatim to the English copies above,
  // carries it too). Each checkpoint's other terms (parameters, revision, licence, notes) are in the copy as printed.
  let footnotes=0,terms=0;
  for(const pfx of ['','zh/']){const zh=pfx==='zh/';
    for(const t of data.tracks){
      const path=pfx+'protocols/'+t.id+'/',where=path+'index.md';
      const html=readFileSync(new URL(path+'index.html',DIST),'utf8'),md=readFileSync(new URL(path+'index.md',DIST),'utf8');
      const ol=sectionHtml(html,'foundation-v9').match(/<h3 class="roadmap-h3" id="v9-footnotes">([^<]*)<\/h3>\s*<ol class="fm-footnotes">([\s\S]*?)<\/ol>/);
      assert.ok(ol,path+': the v9 row footnotes');
      const page=[...ol[2].matchAll(/<li id="fn-v9-\d+"><span>([^<]*)<\/span>(?:<span class="note-original" lang="en">([^<]*)<\/span>)?<\/li>/g)]
        .map(m=>m[2]===undefined?{text:decodeHtml(m[1])}:{text:decodeHtml(m[1]),original:decodeHtml(m[2])});
      assert.deepEqual(page,[...new Set(FMX.models.map(m=>m.row_footnote))].map(en=>inLang(en,zh)),path+': one footnote per distinct row footnote of the export, in order'+(zh?', in Chinese with the English':''));
      const part=mdSection(md,norm(ol[1]),3);assert.ok(part,where+': the copy has "'+ol[1]+'"');
      const items=part.split('\n').filter(l=>l.startsWith('- '));
      assert.equal(items.length,page.length,where+': as many row footnotes as the page');
      page.forEach((f,i)=>assert.ok(itemIs(items[i],'- ',f),where+': row footnote '+(i+1)+' is the page\'s, verbatim, not "'+items[i].slice(0,100)+'"'));
      footnotes+=page.length;
    }
    for(const f of htmlPages.filter(f=>f.startsWith(pfx+'methods/')&&(zh||!f.startsWith('zh/')))){
      const html=readFileSync(new URL(f,DIST),'utf8');if(!html.includes('id="checkpoints"'))continue;
      const path=f.replace(/index\.html$/,''),where=path+'index.md',md=readFileSync(new URL(path+'index.md',DIST),'utf8');
      const sec=sectionHtml(html,'checkpoints'),h2=sec.match(/<h2 id="checkpoints-heading">([^<]*)<\/h2>/);
      const part=h2&&mdSection(md,norm(h2[1]),2);assert.ok(part,where+': the copy has the checkpoints section');
      const arts=[...sec.matchAll(/<article class="fm-checkpoint" data-checkpoint="([^"]+)">([\s\S]*?)<\/article>/g)];
      assert.ok(arts.length>0,path+': its checkpoints');
      for(const [,id,art] of arts){
        const m=FMX.models.find(x=>x.id===id),name=decodeHtml(art.match(/<h3 lang="en">([^<]*)<\/h3>/)[1]);
        assert.ok(m&&m.name===name,path+': '+id+' is the export\'s '+name);
        const sub=mdSection(part,name,3);assert.ok(sub,where+': the checkpoint '+name);
        const items=sub.split('\n').filter(l=>l.startsWith('- ')),pairs=[...art.matchAll(/<div><dt>([^<]*)<\/dt><dd>([\s\S]*?)<\/dd><\/div>/g)];
        assert.equal(items.length,pairs.length,where+' '+name+': every term the page prints');
        pairs.forEach(([,dt,dd],i)=>{assert.equal(squash(items[i]),squash('- '+dt+': '+blockText(dd)),where+' '+name+': "'+decodeHtml(dt)+'" as the page prints it');terms++;});
        assert.equal(items.filter(l=>itemIs(l,'- '+(zh?'各行脚注':'Row footnote')+': ',inLang(m.row_footnote,zh))).length,1,where+' '+name+': its row footnote, verbatim');
        footnotes++;
      }
    }
  }
  assert.ok(footnotes>=2*(8*13+16)&&terms>=2*16*8,'the row footnotes and checkpoint terms were read ('+footnotes+', '+terms+')');
  // (N3b) v9 counts outside those regions. (1) The transfer-coverage map on /, /zh/, /topics/ and /zh/topics/: every
  // entry's figures bound to its own link line ("…#v9-adaptation) n=36"). (2) The topic cards there: each card's line
  // is the card as printed, its v9 and route-1 counts derived from the exports. (3) The home snapshot note as printed,
  // its counts derived from the export. (4) Every paragraph of each protocol page's #foundation-v9 and of the route-1
  // and v9 topic sections, as printed (whitespace aside), the 126 frozen cells re-counted where rows have intervals. (5) No v9 or route-1 data-fig on any
  // page lies outside a region these checks read.
  const b8=FMX.protocols.find(p=>p.id==='beta-8ch'),b4=FMX.protocols.find(p=>p.id==='beta-4ch');
  const fmModels=FMX.pretraining_exposure.models.filter(m=>m.evaluated_in_v9).length,fmMatrix=FMX.models.filter(m=>m.panel==='matrix').length,fmAbl=FMX.models.filter(m=>m.panel==='masking ablation').length;
  const frozenCells=FMX.frozen_probe.filter(c=>c.status==='complete').length;
  assert.ok(b4.people===b8.people&&fmMatrix+fmAbl===FMX.models.length&&frozenCells===126,'v9: BETA\'s people, the checkpoints and the frozen cells, from the export');
  const cardPinsMd={
    'does-pretraining-help':{en:`${FMX.models.length} further checkpoints`,zh:`另外 ${FMX.models.length} 个检查点`},
    'fewer-electrodes':{en:`BETA, ${b8.channels} and ${b4.channels} electrodes, ${b4.people} people`,zh:`BETA ${b8.channels} 与 ${b4.channels} 个电极，${b4.people} 名被试`},
    'when-not-to-act':{en:`reliable decisions, ${RDX.protocols['arithmetic-rest'].people} and ${RDX.protocols['beta-8ch'].people} people`,zh:`可靠的决策，${RDX.protocols['arithmetic-rest'].people} 与 ${RDX.protocols['beta-8ch'].people} 名被试`}};
  let mapEntries=0,cards=0;
  for(const pfx of ['','zh/']) for(const page of [pfx,pfx+'topics/']){const zh=pfx==='zh/';
    const html=readFileSync(new URL(page+'index.html',DIST),'utf8'),md=readFileSync(new URL(page+'index.md',DIST),'utf8'),where=page+'index.md';
    const a=html.indexOf('<table class="tmap"'),table=html.slice(a,html.indexOf('</table>',a));
    const entries=[...table.matchAll(/<li data-map="([^"]+)"><a href="([^"]+)">([^<]*)<\/a><span class="tmap-n">((?:[^<]|<span[^>]*>[^<]*<\/span>)*)<\/span>/g)];
    assert.ok(entries.length===(table.match(/class="tmap-n"/g)||[]).length&&entries.filter(e=>e[4].includes('foundation-models-update.json')).length===2,page+': every map entry with a figure read, the two v9 entries among them');
    for(const [,key,href,label,n] of entries){
      const line=`[${decodeHtml(label)}](https://bci.report${href}) ${norm(n.replace(/<[^>]+>/g,''))}`;
      assert.ok(new RegExp(esc(line)+'(?![\\d.,])').test(md),where+': the map entry '+key+' carries its figures on its own link ("'+line+'")');mapEntries++;}
    for(const [,href,card] of html.matchAll(/<a class="topic-entry-card" href="([^"]+)">([\s\S]*?)<\/a>/g)){
      const h4=decodeHtml(card.match(/<h([34])>([^<]*)<\/h\1>/)[2]),parts=[...card.matchAll(/<(span class="family"|p|small)>([\s\S]*?)<\/(?:span|p|small)>/g)].map(m=>norm(m[2].replace(/<[^>]+>/g,' ')));
      const line=md.split('\n').find(l=>l.startsWith(`- [${h4}](https://bci.report${href}): `));
      assert.ok(line,where+': the card "'+h4+'"');
      assert.equal(norm(line),norm(`- [${h4}](https://bci.report${href}): ${parts.join(' · ')}`),where+': the card "'+h4+'" as the page prints it');
      const slug=href.split('/').at(-2);
      if(cardPinsMd[slug]) assert.ok(line.endsWith(' · '+cardPinsMd[slug][zh?'zh':'en']),where+': the '+slug+' card ends "'+cardPinsMd[slug][zh?'zh':'en']+'", counted from the export');
      cards++;
    }
  }
  assert.ok(mapEntries>=4*16&&cards===4*topicPages.length,'the map entries and topic cards were read ('+mapEntries+', '+cards+')');
  for(const pfx of ['','zh/']){const zh=pfx==='zh/';
    const html=readFileSync(new URL(pfx+'index.html',DIST),'utf8'),md=readFileSync(new URL(pfx+'index.md',DIST),'utf8');
    const p=html.match(/<p class="matrix-added"[^>]*>([\s\S]*?)<\/p>/)[1],para=md.split('\n\n').find(b=>b.startsWith(zh?`另外 ${fmMatrix} 个基础模型编码器，`:`${fmMatrix} further foundation encoders, `));
    assert.ok(para&&norm(para)===norm(blockText(p)),pfx+'index.md: the snapshot note as the page prints it');
    const ran=FMX.frozen_probe.filter(c=>c.model==='brainomni-base'&&c.status==='complete').length;
    for(const s of zh?[`另外 ${fmMatrix} 个基础模型编码器`,`BrainOmni Base 只在其中 ${ran} 个上运行`,`它们是 ${fmModels} 个模型的检查点；其中一个模型另有 ${fmAbl} 个检查点组成掩码消融，共 ${fmMatrix+fmAbl} 个。`]
                     :[`${fmMatrix} further foundation encoders`,`BrainOmni Base on ${['zero','one','two','three','four','five','six','seven'][ran]} of them`,`They are checkpoints of ${fmModels} models; ${fmAbl} more checkpoints of one of them form a masking ablation, ${fmMatrix+fmAbl} in all.`])
      assert.ok(para.includes(s),pfx+'index.md: the snapshot note says "'+s+'", counted from the export');
  }
  let paras=0;
  const parasCarried=(path,id,where,pins=[])=>{
    const html=readFileSync(new URL(path+'index.html',DIST),'utf8'),md=readFileSync(new URL(path+'index.md',DIST),'utf8');
    const sec=sectionHtml(html,id),h=sec.match(/<h([23])\b[^>]*>([\s\S]*?)<\/h\1>/),part=mdSection(md,norm(h[2].replace(/<[^>]+>/g,' ')),Number(h[1]));
    const flat=squash(part);
    // From the heading on: an eyebrow above it is printed before the copy's heading line.
    for(const [,p] of blockText(sec.slice(h.index+h[0].length).replace(/<p\b[^>]*>/g,'\u0001').replace(/<\/p>/g,'\u0002')).matchAll(/\u0001([^\u0001\u0002]*)\u0002/g)){
      if(!squash(p))continue;
      assert.ok(flat.includes(squash(p)),where+': index.md #'+id+' lacks the paragraph "'+norm(p).slice(0,90)+'…" as the page prints it');paras++;}
    for(const s of pins) assert.ok(part.includes(s),where+': index.md #'+id+' says "'+s+'"');
  };
  for(const pfx of ['','zh/']){const zh=pfx==='zh/';
    for(const t of data.tracks) parasCarried(pfx+'protocols/'+t.id+'/','foundation-v9',pfx+'protocols/'+t.id,
      t.type==='tradeoff'?[]:[zh?`冻结单元格共有 ${frozenCells} 个，偶尔出现不重叠，本身就在随机误差的预料之中`:`with ${frozenCells} frozen cells an occasional non-overlap is expected by chance`]);
    parasCarried(pfx+'topics/when-not-to-act/','reliable-decisions',pfx+'when-not-to-act');
    parasCarried(pfx+'topics/does-pretraining-help/','v9-encoders',pfx+'does-pretraining-help');
    parasCarried(pfx+'topics/fewer-electrodes/','v9-montage',pfx+'fewer-electrodes');
    for(const id of ['design','motor-imagery','sleep','eesm19','secondary','methods-and-limits']) parasCarried(pfx+'topics/shared-encoder/',id,pfx+'shared-encoder');
  }
  // Review of 2026-10-07: the copies of every BOAS region carry its conditions. The checks above read figures, and
  // paragraphs of the topic page only, so a gap line dropped from a copy (and with it from llms-full.txt, which holds the
  // English copies verbatim) passed. Each BOAS section or group in a copy holds, once per gaps block the page prints
  // there, the three gaps (in Chinese with the English), "pseudonymised", what is not evaluated and the credit.
  {
    const srx=JSON.parse(readFileSync(new URL('data/shared-representation-update.json',DIST),'utf8')),BC=srx.results['one-representation'].boas_conditions;
    const SRZB=(()=>{const c={shared:srx};vm.runInNewContext(stripTypeScriptTypes(readFileSync(new URL('../src/data/shared-encoder.ts',import.meta.url),'utf8'))
      .replace(/^import[^\n]*\n/gm,'').replace(/^export /gm,'')+'\nthis.srZh=srZh;',c);return c.srZh;})();
    let boasCopies=0;
    for(const pfx of ['','zh/']){const zh=pfx==='zh/';
      const items=[...BC.gaps.flatMap(g=>zh?[SRZB[g],g]:[g]),zh?'被试在公开发布中是假名化的。':'Participants are pseudonymised in the public release.',
                   ...(zh?[SRZB[BC.not_an_evaluation_of],BC.not_an_evaluation_of]:[BC.not_an_evaluation_of]),BC.attribution];
      assert.ok(items.every(t=>typeof t==='string'&&t.length>10),pfx+': the BOAS conditions to look for');
      for(const [path,id] of [['topics/shared-encoder/','sleep'],['topics/shared-encoder/','secondary'],['datasets/boas/','g-shared-encoder'],
                              ['methods/eegnet/','g-boas-shared-encoder'],['methods/cbramod/','g-boas-shared-encoder']]){
        const html=readFileSync(new URL(pfx+path+'index.html',DIST),'utf8'),md=readFileSync(new URL(pfx+path+'index.md',DIST),'utf8'),where=pfx+path+'index.md #'+id;
        const sec=sectionHtml(html,id);assert.ok(sec,where+': the section renders');
        const blocks=(sec.match(/data-boas-gaps="true"/g)||[]).length;assert.ok(blocks>0,where+': the page prints BOAS\'s conditions here');
        const h=sec.match(/<h([23])\b[^>]*>([\s\S]*?)<\/h\1>/),part=mdSection(md,norm(h[2].replace(/<[^>]+>/g,' ')),Number(h[1]));
        assert.ok(part,where+': the copy has the section');
        const flat=squash(part);
        for(const t of items){const k=flat.split(squash(t)).length-1;
          assert.ok(k>=blocks,where+': "'+t.slice(0,60)+'" '+k+' times, for '+blocks+' gaps block(s) on the page');}
        boasCopies++;
      }
    }
    assert.equal(boasCopies,10,'the BOAS regions of the copies were read');
  }
  // (5) Every v9 and route-1 data-fig on every page sits in a region a copy check reads.
  const read=[/^(?:zh\/)?protocols\/[^/]+\/index\.html#foundation-v9$/,/^(?:zh\/)?topics\/when-not-to-act\/index\.html#reliable-decisions$/,/^(?:zh\/)?topics\/does-pretraining-help\/index\.html#v9-encoders$/,
    /^(?:zh\/)?topics\/fewer-electrodes\/index\.html#v9-montage$/,/^(?:zh\/)?(?:datasets|methods)\/[^/]+\/index\.html#g-[^#]*(?:reliable-decisions|foundation-v9|v9-adaptation)$/,
    /^(?:zh\/)?methods\/[^/]+\/index\.html#checkpoints$/,/^(?:zh\/)?(?:topics\/)?index\.html#tmap$/,/^(?:zh\/)?methods\/index\.html#model-card$/,
    // Route 2 (2026-10-07): its question's sections and its groups.
    /^(?:zh\/)?topics\/shared-encoder\/index\.html#(?:motor-imagery|sleep|eesm19|secondary|methods-and-limits)$/,/^(?:zh\/)?(?:datasets|methods)\/[^/]+\/index\.html#g-[^#]*shared-encoder$/];
  let located=0;
  for(const f of htmlPages){const html=readFileSync(new URL(f,DIST),'utf8');
    for(const m of html.matchAll(/data-fig="(?:foundation-models-|reliable-decisions-|shared-representation-)[^"]*"/g)){
      const before=html.slice(0,m.index),open=[];
      for(const x of before.matchAll(/<(section|table|article)\b([^>]*)>|<\/(section|table|article)>/g)){
        if(x[3]){open.pop();continue;}
        open.push(x[1]==='table'&&/class="tmap"/.test(x[2])?'tmap':x[1]==='article'&&/class="model-card"/.test(x[2])?'model-card':(x[2].match(/\sid="([^"]+)"/)||[])[1]||'');}
      assert.ok(open.some(id=>read.some(re=>re.test(f+'#'+id))),f+': the figure '+m[0]+' lies outside every region the copy checks read');located++;}
  }
  // The methods hub's model cards: each card's figures in its own subsection of the copy, as printed.
  for(const pfx of ['','zh/']){
    const html=readFileSync(new URL(pfx+'methods/index.html',DIST),'utf8'),md=readFileSync(new URL(pfx+'methods/index.md',DIST),'utf8');
    for(const [,card] of html.matchAll(/<article class="model-card"[^>]*>([\s\S]*?)<\/article>/g)){
      if(!card.includes('data-fig="foundation-models-'))continue;
      const name=norm(card.match(/<h3\b[^>]*>([\s\S]*?)<\/h3>/)[1].replace(/<[^>]+>/g,' ')),sub=mdSection(md,name,3);
      assert.ok(sub,pfx+'methods/index.md: the card '+name);
      const fig=card.match(/<p class="parameter">([\s\S]*?)<\/p>/);
      assert.ok(fig&&sub.split('\n').some(l=>squash(l)===squash(blockText(fig[1]))),pfx+'methods/index.md: '+name+' carries its parameters as printed ("'+(fig&&norm(blockText(fig[1])))+'")');}
  }
  console.log('PASS: 2026-10-05 second follow-up review — '+footnotes+' row footnotes verbatim in the copies (REVE\'s sensitivity runs with their direction), '+terms+' checkpoint terms, '+mapEntries+' map entries bound to their links, '+cards+' topic cards and the home snapshot note as printed with their counts from the exports, '+paras+' paragraphs of the route-1 and v9 sections (126 frozen cells), and '+located+' v9 and route-1 figures, each inside a region a copy check reads.');
  console.log('PASS: 2026-10-05 review — the route-1 and v9 sections and entity groups carry every printed figure into their Markdown copies, in order ('+checked+' figures); llms-full.txt holds every English copy verbatim; the home page\'s v9 and ablation rows ('+homeRows+') and every topic\'s short answer ('+answers+') carry the page\'s figures into the copies, in order.');
}
// --- 2026-10-05 follow-up review: a v9 figure prints as decimal rounding gives it --------------------
// A difference of two proportions carries the binary noise of both: BrainOmni's BETA change is exactly
// (1451 − 2431) / 11200 = −0.0875, but was stored as −0.08749999999999997 and printed −8.7 pp where the candidate's
// −8.75 gives −8.8. The export now stores every difference it derives rounded to 12 decimals (as the CSVs store
// percents) and checks each against the candidate's stated value; held here: those differences are stored at 12
// decimals, and every one-decimal v9 JSON figure on every page prints as the half-up rounding of its stored value's
// 12-decimal form, so no float artefact can flip a printed digit.
{
  const FMJ='foundation-models-update.json';
  const C=JSON.parse(readFileSync(new URL('data/'+FMJ,DIST),'utf8')).results['foundation-models-v9'].comparisons;
  const derived=[...C.base_vs_large.map(x=>x.large_minus_base),...C.fewer_electrodes_beta.map(x=>x.four_minus_eight)];
  assert.equal(derived.length,21+16,'every v9 derived difference');
  // 100·v at one decimal, rounded half up on v's 12-decimal form (integers below 2^53 throughout).
  const tenths=v=>{const u=Math.round(Math.abs(v)*1e12),t=Math.floor((u+5e8)/1e9);return Math.floor(t/10)+'.'+(t%10);};
  const want={pct1:v=>(v<0?'-':'')+tenths(v)+'%',pp1:v=>(v>=0?'+':'−')+tenths(v)+' pp',sgn1:v=>(v>=0?'+':'−')+tenths(v)};
  let n=0;
  for(const f of htmlPages){
    const html=readFileSync(new URL(f,DIST),'utf8');
    for(const [,format,raw,text] of html.matchAll(/data-fig="foundation-models-update\.json\|(pct1|pp1|sgn1)\|([^"]+)"[^>]*>([^<]*)</g)){
      assert.equal(text,want[format](Number(raw)),f+': the v9 figure '+raw+' prints "'+text+'", not its decimal rounding');n++;}
  }
  assert.ok(n>500,'the v9 one-decimal figures were read ('+n+')');
  for(const v of derived) assert.equal(Number(v.toFixed(12)),v,'a v9 derived difference is stored rounded to 12 decimals, not '+v);
  // The case the review found, on both topic pages that print it, in both languages.
  for(const p of ['','zh/']) assert.ok(readFileSync(new URL(p+'topics/fewer-electrodes/index.html',DIST),'utf8').match(/data-fig="foundation-models-update\.json\|pp1\|-0\.0875"[^>]*>−8\.8 pp</),p+'fewer-electrodes: BrainOmni\'s change prints −8.8 pp');
  console.log('PASS: 2026-10-05 follow-up review — v9 derived differences stored at 12 decimals; '+n+' one-decimal v9 figures print as decimal rounding of their stored values (BrainOmni −8.8 pp).');
}
console.log('PASS: 2026-10-04 v9 foundation models, topics — does-pretraining-help #v9-encoders (sleep rows above every published row, BETA above CBraMod and not above CCA, the EEGMAT adaptation with verdicts and LoRA budgets, REVE Base against Large with marginal intervals and no paired test, the masking ablation) and fewer-electrodes #v9-montage (BETA eight to four beside the released rows, six-channel sleep, no small-montage advantage, no new row above standard CCA at four electrodes, the overlapping rows named): every figure from its file on a row naming its protocol, tokens pinned, the same in both languages, family order, the export\'s relations and claims, chance flags, exposure badges and ZUNA 1.1\'s sentence, limits, licences; model-adaptation\'s figure-free pointer; release log and sitemap.');
console.log('PASS: 2026-10-04 v9 foundation models, pages — every protocol page with its v9 section (each row its CSV row, in family order, never re-sorted; not run with its reason, no figure; chance flags by the core rule and the CSV; exposure statement, badge and source from the exposure table, ZUNA 1.1 unknown everywhere; footnotes, licences, research-use sentence; masking ablation collapsed; EEGMAT adaptation with verdicts on arithmetic-rest; LaBraM and CBraMod sourced beside the released sentence); the home table\'s embedded rows equal the CSVs, first paint equals the render, dialogs carry the caveats; directory cards with the export\'s statuses, licences and parameters, REVE Base evaluated, MIRepNet and EEG-DINO catalogue only; method pages with groups, checkpoints, terms and exposure; Measured-on lines; dataset groups; topic and data-use wording; hub counts; release log; sitemap.');
console.log('PASS: 2026-10-04 route 1, reliable decisions — its own section before the roadmap; every figure from its export, the same in both languages; each coverage beside the people with nothing accepted; nothing accepted is not defined, fewer than ten a flagged count; every contrast with the verdict its interval supports; methods unranked; certified risk a nominal guarantee with folds over target; labels per new person; LoRA sentence; raw quality not applicable, never zero; robustness panel collapsed with ds003810 crude, sensitivity arms as fold counts, idle and BNCI2015-001 figure-free; required limitations; credits; dataset and method groups; markup, releases and data use.');

console.log('PASS: Chinese register — licence and rights-review notes with their English beside them, model notes in Chinese; chart colours equal the legend swatches.');
console.log('PASS: 2026-10-02 discoverability — share card is the recorded badge-free bitmap with alt/size on every page; home Dataset cites the newest release with every file and topic part; Atom feed matches the release log; only /data/* is cross-origin; cite blocks name exactly their releases, in both languages and Markdown; table names survive into Markdown; footers, llms.txt, licences and .zenodo.json agree.');
console.log('PASS: dataset, method and API pages — every figure re-read from its served file, bilingual parity, Markdown copies carry every figure, llms.txt complete, IndexNow key, no held source anywhere.');
console.log('PASS: short answers — question as h1 and title, every answer figure shown in the evidence below it, FAQPage equal to the printed answer.');
console.log('PASS: coverage matrix, '+topicPages.length+' topic pages, track changes, family filtering, sorting, empty state, dialogs, invalid inputs, export counts and English-only data.');
console.log('PASS: Chinese pages — lang, reciprocal hreflang, self canonical, every figure equal to English, credits kept, CSP, payload untranslated.');
console.log('PASS: 2026-10-01 adaptation, on its own topic since 2026-10-02 — arm, contrast, seed and cost figures equal the audited export; matrix readout beside the head-only arm, marked and its release cited; no winner between LoRA and last block; next-day section figure-free with the BNCI2015-001 and cross-session statuses; labelled on card, snippets, answer and entity groups; calibration-budget keeps figure-free notes at the old anchors; corrections listed; API example runs; no stage label.');
console.log('PASS: 2026-09-27 context — PC/VR, gait and non-control figures equal the audited export; no same-display claim; comparator beside gait; coverage beside conditional accuracy; no held source named.');
console.log('PASS: 2026-09-27 when not to act — idle figures from the reviewed protocol; roadmap a figure-free plan with one status per route (route 1 run, results above; routes 2 and 3 not run, since 2026-10-04); releases list every served file with its true SHA-256.');
console.log('PASS: 2026-09-23 clinical — comparator marked, claim boundary stated, demographics and withheld descriptors absent, holds carry no figures.');
console.log('PASS: 2026-09-22 evidence — Alpha Waves released with credits, no per-person values, R² unclamped, roadmap stays planned.');
// --- The later-sessions question (owner decision, 2026-10-08) ----------------------------------------------------
// /topics/later-sessions/: does a decoder trained on an earlier session still work later? Four results from the
// large-source batch — WBCIC-SHU (two CPU baselines; frozen CBraMod), the longitudinal RSVP source and Forenzo's
// continuous cursor tracking (a negative result) — each from later-sessions-update.json. The topic data-fig loop
// re-reads every figure from the export; pinned here: (1) each table cell, chart row and reading carries the export's
// own figures in its own place; (2) English and Chinese print the same figures; (3) the handoffs' required caveats are
// on the page in both languages; (4) online control, intended motion, a ranking or leaderboard and a pooled score
// appear only in a denial, and Jev nowhere; (5) the result sections type no figure of their own, so no per-person
// value can enter outside the export, and the only medians are the four Forenzo ridge medians; (6) the related holds
// and statuses print no figure; (7) the cite block names this release alone, and the Markdown copy carries every
// figure in order; (8) does-pretraining-help's one pointer is figure-free; the card and the map count people only
// where the export does, and Forenzo's records are never printed as people.
{
  const LTS='later-sessions-update.json',R=LTX.results;
  const cpu=R['wbcic-cross-session-cpu'],fm=R['wbcic-frozen-cbramod'],rs=R['rsvp-later-visits'],fz=R['forenzo-continuous-control'];
  const wide=x=>Math.abs(x)>=1000?'int0':x!==0&&Math.abs(x)<0.01?'sig3':'num3';
  const fmtOf={pct1:fmt.pct1,pp1:fmt.pp1,sgn1:fmt.sgn1,sgn3:fmt.sgn3,auc3:fmt.auc3,num3:fmt.num3,count:fmt.count,int0:fmt.int0,sig3:fmt.sig3};
  // A figure as printed: its attribute and its text, so a cell holds the leaf and prints it in its format.
  const has=(h,f,x)=>new RegExp(`data-fig="${LTS.replace(/\./g,'\\.')}\\|${f}\\|${String(x).replace(/[.+-]/g,'\\$&')}"[^>]*>${fmtOf[f](x).replace(/[.+]/g,'\\$&')}<`).test(h);
  const figAttrs=h=>[...h.matchAll(/data-fig="([^"]+)"/g)].map(m=>m[1]);
  const spanEnd=(h,at)=>{const tag=h.slice(at+1).match(/^\w+/)[0],re=new RegExp(`<${tag}\\b|</${tag}>`,'g');re.lastIndex=at;let d=0,m;
    while((m=re.exec(h))){d+=m[0].startsWith('</')?-1:1;if(!d)return m.index;}return h.length;};
  const el=(h,sel,where)=>{const a=h.search(sel);assert.ok(a>=0,where+': '+sel+' renders');return h.slice(a,spanEnd(h,a));};
  const vis=h=>decodeHtml(h.replace(/<[^>]+>/g,' ')).replace(/\s+/g,' ').trim();
  const cohorts=['2C','3C'],fzC=['Main','Transfer Learning'],fzA=['historical_decoder_velocity_imitation','constructed_raw_target_displacement_proxy'];
  const releaseId=LTX.release_id;
  let pinned=0;
  const pages={};
  for(const [label,pfx] of [['en',''],['zh','zh/']]){
    const zh=label==='zh',path=pfx+'topics/later-sessions/',where=path,html=pageOf(path);
    const main=html.slice(html.indexOf('<main'),html.indexOf('<section class="cite-page"'));
    pages[label]=main;
    // Every figure on the page is a leaf of this export, and nothing else is cited.
    assert.ok(figAttrs(main).length>300&&figAttrs(main).every(a=>a.startsWith(LTS+'|')),where+': every figure is a leaf of '+LTS);
    const cite=html.slice(html.indexOf('<section class="cite-page"'));
    assert.equal(cite.match(/data-releases="([^"]+)"/)[1],releaseId,where+': the cite block names this release alone');
    assert.ok(html.includes('href="/data/'+LTS+'"')&&vis(el(main,/<p class="citation-note">(?:Data source:|数据来源：)/,where)).match(/^(?:Data source:|数据来源：) later-sessions-update\.json · schema bci-report-later-sessions-update-v1[.。]$/),where+': the data-source note names the file and its schema, and no date');
    // (1) WBCIC-SHU: each cohort's three decoders, the two paired differences, the trial and session accounting.
    const wb=el(main,/<section\b[^>]*\sid="wbcic-shu"/,where);
    for(const c of cohorts){
      const P=cpu.cohorts[c],M=fm.cohorts[c];
      const cell=k=>el(wb,new RegExp(`<td data-cell="${c}\\|${k}"`),where+' '+c+' '+k);
      const pr=cell('source_prior'),rd=cell('relative_spectral_ridge'),cb=cell('frozen_cbramod');
      for(const [h,x] of [[pr,P.arms.source_prior],[rd,P.arms.relative_spectral_ridge],[cb,M.frozen_cbramod]]){
        assert.ok(has(h,'pct1',x.balanced_accuracy.mean)&&has(h,'pct1',x.accuracy.mean)&&has(h,'pct1',x.macro_f1.mean),where+': '+c+' balanced accuracy, accuracy and macro F1');pinned+=3;}
      for(const [h,x] of [[rd,P.arms.relative_spectral_ridge],[cb,M.frozen_cbramod]]){
        assert.ok(has(h,'pct1',x.balanced_accuracy.interval_95[0])&&has(h,'pct1',x.balanced_accuracy.interval_95[1]),where+': '+c+' interval');pinned+=2;}
      assert.equal(figAttrs(pr).length,3,where+': '+c+' the prior prints no interval (it is a floor, by construction)');
      for(const [k,d] of [['ridge',P.paired],['cbramod',M.paired]]){
        const h=cell('diff-'+k),x=d.balanced_accuracy_difference;
        assert.ok(has(h,'pp1',x.mean)&&has(h,'sgn1',x.interval_95[0])&&has(h,'pp1',x.interval_95[1]),where+': '+c+' '+k+' paired difference and interval');pinned+=3;
        assert.equal(vis(h).includes(zh?'区间在零以上':'Interval above zero'),d.interval_excludes_zero===true&&x.interval_95[0]>0,where+': '+c+' '+k+' says above zero exactly where the interval is');
      }
      assert.ok(has(wb,'pct1',P.chance_level)&&has(wb,'count',P.people)&&has(wb,'count',P.source_trials)&&has(wb,'count',P.target_trials),where+': '+c+' chance, people and trials');
    }
    const q=cpu.session_quality;
    const tn=el(wb,/<p class="protocol-note" data-later-note="wbcic-trials"/,where);
    for(const v of [q.fixed_count_holds,q.sessions,q.delivered_trials,q.nominal_trials,q.holds_in_selected_sessions]) assert.ok(has(tn,'count',v),where+': the session accounting, '+v);
    const fd=el(wb,/<div class="finding" data-finding="wbcic\|2C\|frozen_cbramod"/,where);
    assert.ok(has(fd,'pp1',fm.cohorts['2C'].paired.balanced_accuracy_difference.mean)&&has(fd,'pp1',fm.cohorts['3C'].paired.balanced_accuracy_difference.mean),where+': the finding states both cohorts\' gaps');
    // (1) RSVP: the subtitle as the handoff words it, the model label, a three-point chart with no curve, every measure.
    const rv=el(main,/<section\b[^>]*\sid="longitudinal-rsvp"/,where);
    assert.equal(vis(el(rv,/<h2 id="rsvp-heading"/,where)),zh?'第一次训练的脑电解码器，在后续访次还有效吗？':'Does your decoder still work at later visits?',where+': the RSVP section has the title its handoff gives');
    const sub=el(rv,/<p class="topic-subtitle" data-subtitle="rsvp"/,where);
    assert.ok(rs.subtitle==='Same-person, offline RSVP classification; publisher nominal visit labels; no target-session adaptation.'&&(zh?sub.includes('<span class="note-original" lang="en">'+rs.subtitle+'</span>'):vis(sub)===rs.subtitle),where+': the visible subtitle is the handoff\'s, word for word'+(zh?' (beside its Chinese)':''));
    assert.ok(vis(rv).includes(rs.model.label),where+': the RSVP model label');
    const chart=el(rv,/<figure class="interval-plot" id="rsvp-auroc"/,where);
    const rows=[...chart.matchAll(/<div class="ip-row">([\s\S]*?<div class="ip-value">[\s\S]*?<\/div>)/g)].map(m=>m[1]);
    assert.equal(rows.length,rs.visits.length,where+': the AUROC chart has one point per nominal visit');
    rs.visits.forEach((v,i)=>{assert.ok(has(rows[i],'auc3',v.auroc.mean)&&has(rows[i],'auc3',v.auroc.interval_95[0])&&has(rows[i],'auc3',v.auroc.interval_95[1])&&rows[i].includes('class="ip-ci"'),where+': nominal Day '+v.nominal_day+' AUROC with its interval bar');pinned+=3;});
    assert.ok(!/<path|<polyline|<polygon/.test(chart)&&chart.includes('class="ip-ref"'),where+': no fitted curve, a chance line');
    const rtab=el(rv,/<table data-later-table="rsvp"/,where);
    for(const v of rs.visits){
      const c=k=>el(rtab,new RegExp(`<td data-cell="${v.nominal_day}\\|${k}"`),where+' Day '+v.nominal_day+' '+k);
      assert.ok(has(c('auroc'),'auc3',v.auroc.mean)&&has(c('auroc'),'auc3',v.auroc.interval_95[0])&&has(c('auroc'),'auc3',v.auroc.interval_95[1])
        &&has(c('average_precision'),'auc3',v.average_precision.mean)&&has(c('log_loss'),'num3',v.log_loss.mean)&&has(c('brier_score'),'num3',v.brier_score.mean)
        &&has(c('ece_10_bins'),'num3',v.ece_10_bins.mean)&&has(c('target_events'),'count',v.target_events)&&has(c('target_events'),'count',v.events)&&has(c('target_events'),'pct1',v.target_share),
        where+': nominal Day '+v.nominal_day+', every published measure in its cell');pinned+=10;
      const d=c('delivered_events');
      assert.ok(v.delivered_events===null&&d.includes('data-null="true"')&&!d.includes('data-fig')&&!/\d/.test(vis(d)),where+': Day '+v.nominal_day+' delivered events: null, printed as unavailable, never a zero');
    }
    const ct=el(rv,/<div class="finding" data-finding="rsvp\|contrast"/,where),D=rs.contrast;
    assert.ok(has(ct,'sgn3',D.auroc_difference.mean)&&has(ct,'sgn3',D.auroc_difference.interval_95[0])&&has(ct,'sgn3',D.auroc_difference.interval_95[1])
      &&has(ct,'count',D.people_declined_by_0_05_or_more)&&has(ct,'count',D.people)&&has(ct,'auc3',rs.visits[0].average_precision.mean)&&has(ct,'auc3',rs.visits[2].average_precision.mean),where+': the paired Day 200 minus Day 7 change, its interval, who declined (counted) and AP beside it');pinned+=7;
    // (1) Forenzo: one table per response arm, each cohort's mean, median, comparator and paired interval together.
    const fs=el(main,/<section\b[^>]*\sid="forenzo"/,where);
    assert.ok(vis(el(fs,/<p class="topic-subtitle" data-subtitle="forenzo"/,where)).includes(fz.label),where+': "'+fz.label+'" beside the heading');
    for(const a of fzA){
      const tab=el(fs,new RegExp(`<table data-later-table="forenzo\\|${a}"`),where+' '+a);
      for(const c of fzC){
        const x=fz.cohorts[c].arms[a],row=el(tab,new RegExp(`<tr data-forenzo-cell="${c}\\|${a}"`),where+' '+c+' '+a);
        const td=k=>el(row,new RegExp(`<td data-cell="${k}"`),where+' '+c+' '+a+' '+k);
        for(const [k,m,iv] of [['ridge-mean',x.ridge.primary.mean,x.ridge.primary.interval_95],['comparator',x.source_mean.primary.mean,x.source_mean.primary.interval_95],['paired',x.paired.primary_difference.mean,x.paired.primary_difference.interval_95]]){
          assert.ok(has(td(k),wide(m),m)&&has(td(k),wide(iv[0]),iv[0])&&has(td(k),wide(iv[1]),iv[1]),where+': '+c+' '+a+' '+k+' with its interval');pinned+=3;}
        assert.ok(has(td('ridge-median'),wide(x.ridge.primary.median),x.ridge.primary.median)&&has(td('ridge-median'),'int0',x.upper_tail.ridge_mean_over_median),where+': '+c+' '+a+' the ridge median beside its mean, and how many times over');pinned+=2;
        assert.ok(has(td('paired'),'count',x.paired.records_with_higher_ridge_error)&&has(td('paired'),'count',x.paired.records)&&x.paired.records_with_higher_ridge_error===x.paired.records,where+': '+c+' '+a+' the ridge did worse on every admitted record, counted');
        assert.ok(has(row,'count',fz.cohorts[c].admitted_records)&&has(row,'count',fz.cohorts[c].candidate_records),where+': '+c+' coverage beside the result');
        // A table holds its own arm only: the other arm's figures never sit beside it.
        const other=fz.cohorts[c].arms[fzA.find(o=>o!==a)];
        for(const v of [other.ridge.primary.mean,other.source_mean.primary.mean,other.paired.primary_difference.mean]) assert.ok(!tab.includes(`|${v}"`),where+': '+a+' table carries no figure of the other arm');
      }
      const lab=zh?{historical_decoder_velocity_imitation:'模仿历史解码器（historical decoder imitation）',constructed_raw_target_displacement_proxy:'构造的代理变量（constructed proxy）'}[a]
                  :{historical_decoder_velocity_imitation:'historical decoder imitation',constructed_raw_target_displacement_proxy:'constructed proxy'}[a];
      const box=el(fs,new RegExp(`<div class="forenzo-arm" data-forenzo-arm="${a}"`),where+' '+a);
      assert.ok(vis(el(box,/<h3/,where)).includes(lab)&&vis(el(tab,/<caption/,where)).includes(lab),where+': '+a+' carries its label "'+lab+'" in its heading and its table');
      const tail=el(box,/<figure class="interval-plot" id="forenzo-tail-/,where+' '+a);
      assert.equal((tail.match(/<div class="ip-row">/g)||[]).length,2*3,where+': '+a+' the upper-tail plot shows each cohort\'s ridge mean, median and comparator');
      assert.ok(vis(tail).includes(zh?'对数刻度':'log scale'),where+': '+a+' the tail plot\'s axis is labelled as a log scale');
    }
    const medians=figAttrs(main).filter(a=>fzC.some(c=>fzA.some(x=>a.endsWith('|'+fz.cohorts[c].arms[x].ridge.primary.median))));
    assert.ok(medians.length>=4&&new Set(medians.map(a=>a.split('|')[2])).size===4,where+': the four ridge medians, and no other median (the export holds no other)');
    const cov=el(fs,/<p class="protocol-note" data-later-note="forenzo-coverage"/,where),Mn=fz.cohorts.Main,TL=fz.cohorts['Transfer Learning'];
    for(const v of [Mn.admitted_records,Mn.candidate_records,Mn.held_before_scoring,TL.admitted_records,TL.candidate_records,fz.coverage.admitted_records,...Mn.hold_reasons.map(h=>h.records)]) assert.ok(has(cov,'count',v),where+': the coverage note counts '+v);
    assert.equal(Mn.hold_reasons.length,3,'later-sessions: the export\'s three Main hold reasons');
    if(!zh) for(const h of Mn.hold_reasons) assert.ok(vis(cov).includes(h.reason),where+': the hold reason "'+h.reason+'"');
    for(const v of [fz.coverage.target_rows_per_arm,fz.coverage.response_fits]) assert.ok(has(fs,'count',v),where+': coverage '+v);
    // Secondary metrics: each mean with its interval; the comparator's correlations null, printed as undefined.
    let nulls=0;
    for(const a of fzA) for(const c of fzC) for(const m of ['ridge','source_mean']){
      const row=el(fs,new RegExp(`<tr data-forenzo-secondary="${c}\\|${a}\\|${m}"`),where);
      for(const [k,v] of Object.entries(fz.cohorts[c].arms[a][m].secondary)){
        const td=el(row,new RegExp(`<td data-cell="${k}"`),where);
        if(v.mean===null){assert.ok(td.includes('data-null="true"')&&!td.includes('data-fig')&&!/\d/.test(vis(td)),where+': '+c+' '+a+' '+m+' '+k+' null, never zero');nulls++;}
        else {assert.ok(has(td,wide(v.mean),v.mean)&&has(td,wide(v.interval_95[0]),v.interval_95[0])&&has(td,wide(v.interval_95[1]),v.interval_95[1]),where+': '+c+' '+a+' '+m+' '+k);pinned+=3;}
      }
    }
    assert.equal(nulls,2*2*2,where+': the comparator\'s two correlations, null in every cohort and arm');
    // (3) The handoffs' required caveats, in each language.
    const page=vis(main);
    for(const s of zh?['会话编号只是记录会话的序号，不保证固定的时间间隔','分开分析，从不平均','不能说明它来自预训练','是否出现过 WBCIC-SHU 也没有确定','复用了同样的测试试次','不是全新的测试集','缺失试次的原因不明',
                       '不是给新被试','第 7、80、200 天是发布者的标签','不是某个阈值下的精确率','不是在线选择的成功率','不能说明变化是由时间流逝造成的','Trigger.txt 正好相反',
                       '不是意图中的手部运动，也不是意图控制','不能证明是','从不合并','没有删除、截断或缩尾任何已评分的记录','极端误差的原因','尚未确定','空值，不是零','这里没有训练任何迁移学习模型',
                       '它们的误差也不互相比较','不涉及在线控制质量或意图运动解码','没有做多重比较校正','没有从原始 EEG 独立重做完整的特征提取']
                    :['recording-session ordinals, not a guaranteed time gap','kept apart and never averaged','it does not show that pretraining caused it','whether this checkpoint saw WBCIC-SHU in pretraining is not established','reuses their test trials','not a fresh test set','Why the trials are missing is unknown',
                       'Not a decoder for someone new','Day 7, Day 80 and Day 200 are the publisher’s labels','not precision at a chosen threshold','an online selection success rate','it does not show that elapsed time caused the change','Trigger.txt reverses',
                       'not intended hand motion or intended control','not proven unique people','never pooled','No scored record was removed, clipped or winsorized','what caused the extreme errors','is not established','null, not zero','no transfer-learning model was trained here',
                       'their errors are not compared with each other','no claim about online control quality or intended-motion decoding','no multiple-comparison adjustment','none independently repeated the full feature extraction'])
      assert.ok(page.includes(s),where+': the required caveat "'+s+'"');
    // (4) Forbidden readings appear only as denials; Jev nowhere. ("AUROC ranks targets" is what AUROC measures, not a
    // ranking of decoders, so the verb alone is not read.)
    const sentences=page.split(/(?<=[.;:?])\s+|(?<=[。；：？])/);
    const forbidden=zh?/在线控制|意图运动|意图控制|排行榜|排名|合并|总分|最好|最佳/:/online[- ]control|intended[- ]motion|intended control|intention decoding|leaderboard|\branking\b|\branked\b(?! targets)|\bpool(?:s|ed|ing)?\b|overall score|single score|\bbest\b/i;
    const denial=zh?/不|没有|无|从不|并非|不是/:/\b(?:not|no|never|nor|none|nothing|neither)\b/i;
    for(const t of sentences) if(forbidden.test(t)) assert.match(t,denial,where+': "'+t.slice(0,120)+'" reads as a claim it may only deny');
    // The page's own words: the topic switcher below it is the site's navigation, the same on every topic page.
    const own=main.slice(0,main.indexOf('<nav class="topic-switcher"')),ownMd=readFileSync(new URL(path+'index.md',DIST),'utf8').split(/^(?:Keep exploring|继续探索)$/m)[0];
    assert.ok(own.length>10000&&ownMd.length>5000,where+': the page\'s own content read');
    assert.doesNotMatch(own+ownMd,/\bJev\b/,where+': the page does not mention Jev');
    // (5) The result sections type no figure: every number there is a data-fig leaf, or a label (session and visit
    // numbers, 95%, the 0.05 AUROC threshold, ECE's 10 bins, Chance R01, the log axis's gridlines).
    const allowed=new Set(['0','1','2','3','7','80','200','95%','10','0.05','01','0.01','100','10,000']);
    for(const id of ['wbcic-shu','longitudinal-rsvp','forenzo']){
      const sec=el(main,new RegExp(`<section\\b[^>]*\\sid="${id}"`),where).replace(/<span data-fig="[^"]*"[^>]*>[^<]*<\/span>/g,' ')
        .replace(/<div class="ip-row ip-axis"[\s\S]*?<\/div>\s*<div class="ip-value"><\/div>\s*<\/div>/g,' ').replace(/<code>[\s\S]*?<\/code>/g,' ');
      const typed=[...vis(sec).matchAll(/\d[\d,]*(?:\.\d+)?%?/g)].map(m=>m[0].replace(/,$/,'')).filter(t=>!allowed.has(t));
      assert.deepEqual(typed,[],where+': #'+id+' types a figure outside the export');
    }
    // (6) The related next-day hold and longitudinal status, and the OpenBMI and pretraining links, print no figure.
    const rel=el(main,/<section\b[^>]*\sid="related"/,where);
    assert.ok(!rel.includes('data-fig')&&!/\d/.test(vis(rel)),where+': the related holds and statuses print no figure');
    for(const href of ['/topics/calibration-budget/#next-session','/topics/model-adaptation/#next-day','/topics/model-adaptation/#cross-session','/topics/does-pretraining-help/'])
      assert.ok(rel.includes(`href="${zh?'/zh':''}${href}"`),where+': links '+href);
    // The short answer: the mixed reading, with its limits.
    const ans=vis(el(main,/<section class="short-answer"/,where));
    for(const s of zh?['同一被试的跨会话迁移，不是给新被试解码','不能说明提升来自预训练','标称','阴性结果','每一条纳入记录']:['same-person transfer, not decoding for someone new','does not show that pretraining caused the gain','nominal','a negative result','every admitted record'])
      assert.ok(ans.includes(s),where+': the short answer says "'+s+'"');
    // (7) The Markdown copy carries every figure, in order.
    const md=readFileSync(new URL(path+'index.md',DIST),'utf8');
    let at=0;
    for(const [,t] of main.slice(main.indexOf('<section class="short-answer"')).matchAll(/data-fig="[^"]+"[^>]*>([^<]*)</g)){
      const k=md.indexOf(decodeHtml(t),at);assert.ok(k>=0,where+'index.md: the figure "'+t+'" after offset '+at);at=k+t.length;}
  }
  // (2) The same figures in both languages.
  const ms=h=>figAttrs(h).sort();
  assert.deepEqual(ms(pages.zh),ms(pages.en),'later-sessions: the Chinese page prints exactly the English page\'s figures');
  // (8) does-pretraining-help: one pointer, no figure from this export, no citation of its release.
  for(const pfx of ['','zh/']){
    const h=pageOf(pfx+'topics/does-pretraining-help/'),w=pfx+'topics/does-pretraining-help/';
    const body=h.slice(h.indexOf('<main'),h.indexOf('<nav class="topic-switcher"'));
    assert.equal((body.match(/href="(?:\/zh)?\/topics\/later-sessions\/[^"]*"/g)||[]).length,1,w+': one low-key pointer to the later-sessions question (the switcher aside)');
    assert.ok(body.includes(`<p class="citation-note" data-later-pointer="true">`),w+': the pointer is a citation note');
    assert.ok(!h.includes('data-fig="'+LTS)&&!h.slice(h.indexOf('<section class="cite-page"')).includes(releaseId),w+': the pointer prints no figure and cites nothing new');
  }
  // The card sits under Transfer and counts people only where the export does; the map prints no n for Forenzo.
  for(const pfx of ['','zh/']) for(const page of [pfx,pfx+'topics/']){
    const h=pageOf(page),grp=el(h,/<div class="topic-group" id="group-transfer"/,page);
    const card=el(grp,new RegExp(`<a class="topic-entry-card" href="${pfx?'/zh':''}/topics/later-sessions/"`),page+' card');
    const nums=[...vis(card.replace(/<span class="topic-number"[^>]*>\d+<\/span>/,'')).matchAll(/\d+/g)].map(m=>Number(m[0]));
    assert.deepEqual(nums,[...cohorts.map(c=>cpu.cohorts[c].people),rs.cohort.people],page+': the later-sessions card counts the WBCIC-SHU cohorts and the RSVP cohort, and no Forenzo record');
    const map=el(h,/<table class="tmap"/,page),li=el(map,/<li data-map="session:forenzo"/,page);
    assert.ok(!li.includes('tmap-n')&&!li.includes('data-fig')&&li.includes('later-sessions/#forenzo'),page+': the Forenzo map entry links its section and prints no n');
  }
  // Forenzo's dataset page prints records, never people.
  for(const pfx of ['','zh/']){
    const h=pageOf(pfx+'datasets/forenzo-continuous-tracking/');
    assert.ok(!/<td>\d+<\/td>/.test(h)&&!h.includes(pfx?'没有人类被试':'no human participants')&&(h.match(/条记录，不能证明是不同的人|records, not proven unique people/g)||[]).length===12,pfx+'datasets/forenzo-continuous-tracking/: every row counts records, not people');
  }
  assert.ok(pinned>300,'later-sessions: figures pinned to their cells ('+pinned+')');
  console.log(`PASS: later sessions — /topics/later-sessions/ in both languages: ${pinned} figures pinned to their cells from ${LTS}, the same figures in English and Chinese; WBCIC-SHU's two cohorts apart with priors and paired intervals; the RSVP subtitle word for word, three AUROC points with intervals and no curve, AP beside AUROC, delivered events null; Forenzo per cohort and arm in separate tables with mean, median, comparator and paired interval, coverage, nulls kept; required caveats present, forbidden readings only denied, no typed figure, holds figure-free, no Jev; one figure-free pointer from does-pretraining-help; Forenzo counted as records.`);
}
// --- No update date and no version label in the site's text (owner decision 2026-10-08) ---------------------------
// The site does not say when it was updated or which version it is: the release log does. Every built page, in both
// languages — its HTML (visible text, and aria-label, title and alt) and its Markdown copy — and llms.txt and
// llms-full.txt are read for an update marker ("updated <date>", "Added <date>", "since <date>", "Held since",
// "run on <date>", a "· reviewed <date>" label, "snapshot <date>", "this update", "generated <date>") or an internal
// version label ("v9", "(v9", "release v9", 第九轮), and a data-source note may carry no date at all.
// Kept on purpose, and so left out here: /releases/ and releases.xml (dates and release ids); each page's "Cite this
// page" block and the /api/ BibTeX (release ids and their dates); evidence dates ("checked … on <date>", "Rights
// reviewed <date>", "Status checked <date>", an upstream snapshot's acquisition date, an owner's decision or licence
// acceptance), which no pattern below targets; dataset, licence and model versions (OpenNeuro 1.0.3, Figshare v3,
// REVE licence v1.0, protocol ids …-v1), which the version pattern does not match; and /data-use/'s policy dates.
{
  const MONTH='(?:January|February|March|April|May|June|July|August|September|October|November|December)';
  const DAY=`\\d{1,2} ${MONTH}`,ISO='20\\d\\d-\\d\\d-\\d\\d',ZHD='20\\d\\d 年 \\d+ 月 \\d+ 日';
  const rules=[
    ['an "updated" date',new RegExp(`\\b[Uu]pdated:? (?:on )?(?:20\\d\\d|${DAY})|· [Uu]pdated\\b|\\bUpdate, 20\\d\\d|更新于|${ISO} ?更新|\\d+ 月 \\d+ 日更新`)],
    ['an "added" date',new RegExp(`\\b[Aa]dded:? (?:on )?(?:20\\d\\d|${DAY})|新增于|${ISO} ?新增|${ZHD}(?:新增|加入)`)],
    ['a "since" date',new RegExp(`\\b[Ss]ince (?:${ISO}|${DAY})|(?<!来)自 ?20\\d\\d|\\d+ 月 \\d+ 日起[，,：:]`)],
    ['"held since"',/[Hh]eld since|起暂缓/],
    ['a "run on" date',new RegExp(`\\b(?:[Rr]un|[Rr]an|replayed) on (?:${ISO}|${DAY})|于 ${ZHD}运行|\\d+ 月 \\d+ 日已?运行`)],
    ['a "reviewed <date>" label',new RegExp(`· [Rr]eviewed (?:on )?(?:${ISO}|${DAY})|· ${ZHD}审核`)],
    ['a "snapshot <date>" label',new RegExp(`\\b[Ss]napshot (?:${ISO}|${DAY})|快照 ?(?:${ISO}|${ZHD})`)],
    ['"this update"',/\b[Tt]his update\b|本次更新|这次更新/],
    ['a "generated" date',new RegExp(`\\bgenerated:? (?:on )?(?:20\\d\\d|${DAY})|生成于 ?20\\d\\d`)],
    ['a version label',/(?<![\w.\/#-])(?<!Figshare(?: record)?(?: \d+)? )v\d+(?![\w.]|-\d)|\brelease v\d|第[一二三四五六七八九十]+轮/],
  ];
  const anyDate=new RegExp(`${ISO}|${ZHD}|${DAY} 20\\d\\d`);
  // Phrases still printed while an edit is outstanding, each leaving this list when its edit lands; the PASS line
  // counts the ones still printed. Empty: the data modules' group titles (entities.ts), the /api/ file descriptions
  // (files.ts) and the two dated hold outcomes on the home cards (releases.ts `card`, which index.astro prints in
  // place of the outcome; the register keeps the dated one) no longer carry a date or a version label.
  const pending=[];
  // Kept: the export's own not-run reason, printed as released (foundation-models-update.json); its Chinese carries no version label.
  const verbatim=['LUNA Large is frozen probes only in the v9 stage specification'];
  // /data-use/'s policy dates: the review each source was added under, and a status-only source's released reason.
  const policy={'/data-use/':[new RegExp(`Sources added ${DAY} 20\\d\\d`,'g'),/replayed on 2026-09-22/g]};
  const KEEP_PAGES=new Set(['/releases/','/zh/releases/']);
  const pendingSeen=new Set(),bad=[];
  const scrub=(text,path)=>{
    let t=text;
    for(const p of pending) if(t.includes(p)){pendingSeen.add(p);t=t.split(p).join(' ');}
    for(const p of verbatim) t=t.split(p).join(' ');
    for(const re of policy[path]??[]) t=t.replace(re,' ');
    return t;
  };
  // Link targets are not text: an anchor such as #v9-licences stays, as every link does.
  const scan=(text,where,path)=>{
    const t=scrub(text.replace(/\]\([^)\s]*\)/g,']()').replace(/https?:\/\/\S+/g,' '),path);
    for(const [what,re] of rules){const m=t.match(re);
      if(m) bad.push(`${where}: ${what} — “…${t.slice(Math.max(0,m.index-50),m.index+m[0].length+30).replace(/\s+/g,' ')}…”`);}
  };
  const decode=s=>s.replace(/&#x([0-9a-f]+);/gi,(_,h)=>String.fromCodePoint(parseInt(h,16))).replace(/&#(\d+);/g,(_,d)=>String.fromCodePoint(Number(d)))
    .replace(/&(amp|lt|gt|quot|apos|nbsp);/g,(_,e)=>({amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' '})[e]);
  const cutCiteMd=md=>md.replace(/^## (?:Cite this page|引用本页)\n[\s\S]*?(?=^---$|(?![\s\S]))/m,'');
  const walk=rel=>readdirSync(new URL(rel,DIST),{withFileTypes:true}).flatMap(d=>d.isDirectory()
    ?(['_astro','data'].includes(d.name)&&rel===''?[]:walk(rel+d.name+'/')):[rel+d.name]);
  const files=walk('');
  let nHtml=0,nMd=0;
  for(const f of files.filter(f=>/(?:^|\/)index\.(?:html|md)$|^404\.html$/.test(f))){
    const path='/'+f.replace(/index\.(?:html|md)$/,'').replace(/^404\.html$/,'404');
    if(KEEP_PAGES.has(path)) continue;
    const raw=readFileSync(new URL(f,DIST),'utf8');
    if(f.endsWith('.html')){
      const body=raw.replace(/<head>[\s\S]*?<\/head>/,'').replace(/<(script|style)\b[\s\S]*?<\/\1>/g,'')
        .replace(/<section class="cite-page"[\s\S]*?<\/section>/g,'');
      const attrs=[...body.matchAll(/\s(?:aria-label|title|alt)="([^"]*)"/g)].map(m=>m[1]).join(' ¶ ');
      scan(decode(body.replace(/<[^>]+>/g,' ')+' ¶ '+attrs).replace(/\s+/g,' '),f,path);
      // A data-source note names its file and schema, never a date.
      for(const [,note] of body.matchAll(/<p class="citation-note">([\s\S]*?)<\/p>/g)){
        const t=decode(note.replace(/<[^>]+>/g,' ')).replace(/\s+/g,' ').trim();
        if(/^(?:Data source:|数据来源：)/.test(t)&&anyDate.test(t)) bad.push(`${f}: a dated data-source note — “${t}”`);
      }
      nHtml++;
    }else{
      const md=cutCiteMd(raw);
      scan(md,f,path);
      for(const line of md.split('\n')) if(/^(?:Data source:|数据来源：)/.test(line)&&anyDate.test(line)) bad.push(`${f}: a dated data-source note — “${line}”`);
      nMd++;
    }
  }
  // llms.txt: everything but its Cite section, which names the current release and its date.
  const llms=readFileSync(new URL('llms.txt',DIST),'utf8');
  assert.ok(/^## Cite$/m.test(llms),'llms.txt: the Cite section this check leaves out');
  scan(llms.replace(/^## Cite\n[\s\S]*?(?=^## )/m,''),'llms.txt','/llms.txt');
  // llms-full.txt: page by page, as its footers divide it, leaving out the release log and each Cite block.
  const full=readFileSync(new URL('llms-full.txt',DIST),'utf8').split(/^---\nMarkdown copy of (\S+), generated from the published page\..*$/m);
  let nFull=0;
  for(let i=0;i+1<full.length;i+=2){
    const path=new URL(full[i+1]).pathname;
    if(KEEP_PAGES.has(path)) continue;
    scan(cutCiteMd(full[i]),'llms-full.txt '+path,path);nFull++;
  }
  assert.ok(nHtml>=100&&nMd>=100&&nFull>=50,`the update-label check read the pages (${nHtml} HTML, ${nMd} Markdown, ${nFull} llms-full sections)`);
  assert.deepEqual(bad,[],'an update date or version label is printed outside the release log, a Cite block or the kept evidence and policy dates:\n'+bad.slice(0,20).join('\n'));
  console.log(`PASS: no update date or version label — ${nHtml} HTML pages and ${nMd} Markdown copies in both languages, llms.txt and ${nFull} llms-full.txt sections; the release log, Cite blocks, evidence dates and /data-use/ policy dates kept`+
    (pendingSeen.size?`; ${pendingSeen.size} deferred data-module phrase${pendingSeen.size>1?'s':''} still printed (entities.ts, files.ts, releases.ts).`:'.'));
}
console.log('Mocked WebMCP contract passed. Real supported-browser WebMCP integration has not been verified.');
