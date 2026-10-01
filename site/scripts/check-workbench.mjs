// Application-state tests with minimal DOM doubles; this is not browser or WebMCP integration QA.
import assert from 'node:assert/strict';
import {existsSync,readFileSync,readdirSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import vm from 'node:vm';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
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
  assert.equal(output.models.length,t.rows.length);
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

// The seed-sensitivity scope sentence exists in the data; it must be rendered.
tool.execute({trackId:'mi-rest',family:'all'});
get('#open-protocol').events.click();
assert.match(get('#dialog-body').innerHTML,/no best-seed selection/,'protocol dialog must render seedSensitivity.scope');
assert.match(get('#dialog-body').innerHTML,/retained seed is also the highest/,'protocol dialog must state where the retained seed sits');
get('#close-dialog').events.click();
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
assert.match(built,/separate from the deployment topics above/,'homepage must distinguish the topic extension from the 39-comparison matrix');
assert.match(built,/not independent experiments, and not an overall ranking/,'homepage must not inflate repeated conditions into independent experiments');
assert.doesNotMatch(built,/\d+ additional aggregate measurements/,'no summed measurement count across exports that measure different things');
// Every protocol is reachable without JavaScript and without a dropdown.
for(const t of data.tracks){
  assert.ok(built.includes('data-jump="'+t.id+'"'),t.id+': needs a matrix column heading');
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
  ['calibration-budget','How much calibration data does a wearable SSVEP decoder need?'],
  ['when-not-to-act','How often does an EEG decoder fire when nobody is giving a command?'],
  ['does-pretraining-help','Does pretraining help EEG foundation models like LaBraM and CBraMod?'],
];
const dataFileOf=slug=>slug==='fewer-electrodes'?'evidence-update.json'
  :slug==='clinical-groups'?'clinical-update.json'
  :slug==='when-not-to-act'?'experiments.json'
  :slug==='screen-to-vr'?'context-update.json':'deployment-topics.json';
for(const [slug,title] of topicPages){
  const page=DIST+'topics/'+slug+'/index.html';
  const html=readFileSync(new URL(page,import.meta.url),'utf8');
  assert.ok(html.includes('<h1>'+title+'</h1>'),slug+': page title must render in the initial HTML');
  assert.ok(html.includes('href="/data/'+dataFileOf(slug)+'"'),slug+': the reviewed export holding its figures must be reachable');
  assert.ok(html.includes('aria-label="Breadcrumb"'),slug+': breadcrumb is required');
  assert.ok(html.includes('rel="canonical"'),slug+': canonical link is required');
}
const sitemap=readFileSync(new URL(DIST+'sitemap.xml',import.meta.url),'utf8');
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
// The interface and the four topic pages exist in Chinese; /data-use/ does not.
// What translation can break without anything visibly failing is pinned here.
const bilingual=['',...topicPages.map(([slug])=>'topics/'+slug+'/')];
const read=p=>readFileSync(new URL(DIST+''+p+'index.html',import.meta.url),'utf8');
const zhTitles={'dry-vs-wet':'干电极的解码效果能和湿电极一样好吗？','fewer-electrodes':'更少的电极、或耳道内电极，能比得上完整的头皮电极吗？','screen-to-vr':'在屏幕上校准的 P300 解码器，换到 VR 里还管用吗？','on-the-move':'走路或跑步时，EEG 解码还管用吗？','clinical-groups':'静息态 EEG 能把帕金森病患者和对照组区分开吗？','calibration-budget':'可穿戴 SSVEP 解码器需要多少校准数据？','when-not-to-act':'没有人下指令时，EEG 解码器有多常误触发？','does-pretraining-help':'预训练对 LaBraM、CBraMod 这类 EEG 基础模型有帮助吗？'};
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
  assert.ok(zh.includes('<h1>'+zhTitles[slug]+'</h1>'),slug+': Chinese title must render in the initial HTML');
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
};
const chineseOnly=html=>html.replace(/<script[\s\S]*?<\/script>/g,'').replace(/<(\w+)[^>]*\blang="en"[^>]*>[\s\S]*?<\/\1>/g,'');
for(const path of bilingual){
  const zh=chineseOnly(read('zh/'+path));
  for(const [bad,good] of Object.entries(rejected))
    assert.ok(!zh.includes(bad),`zh/${path}: "${bad}" is a rejected rendering — use "${good}"`);
  // A Chinese sentence does not end on an ASCII full stop.
  assert.doesNotMatch(zh,/[一-鿿\d]\.<\/p>/,'zh/'+path+': Chinese sentence ends with an ASCII period');
}
const workbenchSource=readFileSync(new URL('../src/scripts/workbench.ts',import.meta.url),'utf8');
for(const [bad,good] of Object.entries(rejected))
  assert.ok(!workbenchSource.includes(bad),`workbench.ts: "${bad}" is a rejected rendering — use "${good}"`);

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
for(const p of ['topics/fewer-electrodes/','zh/topics/fewer-electrodes/']){
  assert.doesNotMatch(pageOf(p),/34\.8%|70\.9%|54\.4%|81\.6%|52\.2%|73\.3%/,p+': an individual person\'s score leaked');
  assert.doesNotMatch(pageOf(p),/80\.0%|90\.0%|100\.0%|65\.0%|33\.3%|79\.2%|67\.0%|89\.9%|−40\.0 pp|\+30\.0 pp|\+10\.0 pp/,p+': an individual Alpha Waves score leaked');
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
// 2026-10-01 −1.6 pp is also LoRA minus last block on calibration-budget, so
// there it may appear only inside the adaptation section.
for(const p of everyPage.filter(p=>!p.includes('fewer-electrodes')&&p!=='data-use/')){
  let html=pageOf(p);
  if(p.includes('calibration-budget')){
    const a=html.indexOf('id="adaptation"'),b=html.indexOf('id="methods-and-limits"');
    assert.ok(a>0&&b>a,p+': the adaptation section must render before methods and limits');
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
assert.equal(ev.roadmap.peft.status,'planned');
for(const p of ['topics/calibration-budget/','zh/topics/calibration-budget/']){
  const html=pageOf(p);
  // Its exact two-decimal figures. One decimal collides: 65.1% is a CCA value on this page.
  assert.doesNotMatch(html,/56\.34|65\.05/,p+': the unapproved partial-fine-tuning pilot must not appear');
  // Case-insensitive: the first version missed a sentence-initial "In progress".
  assert.doesNotMatch(html,/\bin progress\b|\bunderway\b|\b(?:is|now) running\b|进行中|正在运行|已开始/i,p+': nothing on this page is described as still running');
  assert.ok(html.includes('38,400')&&html.includes('5,819,936'),p+': engineering parameter counts');
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
// Holds: three of them, stated without numbers, on both home pages.
for(const [label,path] of [['en',''],['zh','zh/']]){
  const home=pageOf(path);
  const holds=home.slice(home.indexOf('id="holds"'),home.indexOf('id="overview"'));
  assert.ok(holds.length>400,label+': the holds section must render');
  for(const word of label==='en'?['No score','Held','Described, not scored']:['没有分数','暂缓','只有描述，没有评分'])
    assert.ok(holds.includes(word),label+': hold state "'+word+'" must be shown');
  // A hold has no result. No percentage, and no decimal figure, inside the cards.
  const cards=holds.slice(holds.indexOf('hold-grid'));
  assert.doesNotMatch(cards,/\d+(?:\.\d+)?%|\d\.\d/,label+': a hold must not carry a figure');
  // Every open hold says since when, and the full register is one click away.
  assert.match(holds,label==='en'?/Held since \d+ \w+ 20\d\d/:/20\d\d 年 \d+ 月 \d+ 日起暂缓/,label+': a hold must carry its date');
  assert.ok(holds.includes(label==='en'?'href="/releases/#holds"':'href="/zh/releases/#holds"'),label+': the holds register must be linked');
}
// The withheld six-person descriptors appear nowhere, in any locale.
const lfameMedians=['0.3540','0.3849','0.2303','0.2655','0.2319'];
for(const p of [...everyPage,'topics/clinical-groups/','zh/topics/clinical-groups/'])
  for(const v of lfameMedians)
    assert.ok(!pageOf(p).includes(v.slice(0,5)),p+': a withheld L-FAME descriptor appeared');

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
  assert.match(road,/data-status="proposal"/,label+': roadmap status is proposal');
  assert.match(road,/data-run-status="not_run"/,label+': roadmap run status is not_run');
  assert.match(road,label==='en'?/No experiment in this section has been run/:/本节中的实验都尚未运行/,label+': the roadmap states its status in words');
  // A plan carries no figure: no percentage, no decimal, no speed-up, no ms.
  // Visible text only: arXiv identifiers in link targets are not figures.
  const roadText=road.replace(/<[^>]+>/g,' ');
  assert.doesNotMatch(roadText,/\d+(?:\.\d+)?\s?%|\d\.\d|\d+(?:\.\d+)?\s?[×x]\b|\d+\s?ms\b/,label+': a figure appeared in the roadmap');
  // Wording that would read as done.
  assert.doesNotMatch(road,/calibrated policy|measured uncertainty|经过校准的策略|经过评测的不确定性|we (?:have )?(?:trained|measured|built)/i,label+': the roadmap must not read as completed work');
  // "Jev-style" is prominent by the maintainer's choice (heading, title, card).
  // Wherever it is, the page says what it is not: no Jev integration, no Jev
  // model that reads EEG, no result.
  assert.match(road,/<h2[^>]*>Jev-style/,label+': the roadmap heading names the research track');
  assert.match(html,label==='en'
    ?/not an integration with Jev, not a Jev model that reads EEG, and not a model BCI Report has trained\. There are no results here yet\./
    :/这里既没有接入 Jev，也不是能读 EEG 的 Jev 模型，更不是本站训练出的模型。目前还没有任何结果。/,label+': the Jev scope sentence must stand beside the name');
  assert.ok(road.indexOf('research-scope')<road.indexOf('route-list'),label+': the scope sentence comes before the routes');
}
// A source on hold in any review manifest is not named on any page until the
// hold is lifted — the rule Alpha Waves and the YSU pilot were held under. Read
// from the manifests themselves, so a new hold is covered without a new line here.
const manifests=['publication_review_20260922/evidence-release-manifest.json','publication_review_20260923/clinical-release-manifest.json','publication_review_20260927/context-release-manifest.json']
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
const leavesOf=file=>{if(!leaves.has(file)){const set=new Set();const walk=v=>{if(typeof v==='number')set.add(v);else if(v&&typeof v==='object')Object.values(v).forEach(walk);};
  walk(JSON.parse(readFileSync(new URL('data/'+file,DIST),'utf8')));leaves.set(file,set);}return leaves.get(file);};
const fmt={pct1:r=>(r*100).toFixed(1)+'%',pct1raw:r=>r.toFixed(1)+'%',pp1:r=>(r>=0?'+':'−')+Math.abs(r*100).toFixed(1)+' pp',
  auc3:r=>r.toFixed(3),auc2:r=>r.toFixed(2),num3:r=>r.toFixed(3).replace(/^-/,'−'),count:r=>r.toLocaleString('en-US')};
const entityPages=htmlPages.filter(f=>/(?:^|\/)(?:datasets|methods)\//.test(f));
assert.ok(entityPages.length>=2*(16+9+2),'dataset and method pages, both languages');
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
  for(const [bad,good] of Object.entries(rejected)) assert.ok(!zhText.includes(bad),`zh/${path}: "${bad}" is a rejected rendering — use "${good}"`);
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
for(const [label,path] of [['en','topics/calibration-budget/'],['zh','zh/topics/calibration-budget/']]){
  const html=pageOf(path);
  const sec=html.slice(html.indexOf('id="adaptation"'),html.indexOf('id="methods-and-limits"'));
  for(const a of adr.arms){
    assert.ok(sec.includes('<div class="reading">'+pct1(a.balanced_accuracy.mean)+'</div>'),label+': '+a.id+' score on its card');
    assert.ok(sec.includes(pct1(a.balanced_accuracy.bootstrap_95[0])+'–'+pct1(a.balanced_accuracy.bootstrap_95[1])),label+': '+a.id+' interval');
    assert.ok(sec.includes(a.trainable_parameters.toLocaleString('en-US')),label+': '+a.id+' trainable parameters');
    assert.ok(sec.includes(a.training_seconds_15_fits.toFixed(1)+' s'),label+': '+a.id+' training time');
    for(const s of a.balanced_accuracy.per_seed_means) assert.ok(sec.includes(pct1(s.mean)),label+': '+a.id+' seed '+s.seed);
  }
  for(const m of ['balanced_accuracy','macro_f1']) for(const c of adr.paired_contrasts[m]){
    assert.ok(sec.includes(pp1(c.mean_change)),label+': '+m+' '+c.id+' change');
    assert.ok(sec.includes(ivp(c.bootstrap_95,label==='zh')),label+': '+m+' '+c.id+' interval');
  }
  // The matrix readout sits beside the head-only arm, said to be a different head and not paired.
  assert.ok(sec.includes(matrixLabram.y.toFixed(1)+'%'),label+': the matrix frozen-LaBraM readout is printed for scale');
  assert.match(sec,label==='en'?/not the best a frozen encoder can do[^.]*not a paired comparison/:/并不是冻结编码器能达到的最好结果[^。]*不是配对比较/,label+': the head-only arm is not the best frozen readout');
  // LoRA vs. last block: an interval across zero is reported as no demonstrated difference.
  const lb=adr.paired_contrasts.balanced_accuracy.find(c=>c.id==='lora-r4_minus_last-block');
  assert.ok(lb.bootstrap_95[0]<0&&lb.bootstrap_95[1]>0);
  assert.match(sec,label==='en'?/crosses zero, so neither is shown to be better/:/跨过零，所以无法说明哪一个更好/,label+': LoRA vs. last block');
  assert.doesNotMatch(html,label==='en'?/LoRA (?:is|was) (?:better|best)|outperform/i:/LoRA 更好(?!，)|优于最后/,label+': no winner is declared');
  // Memory was recorded only as lower bounds; none is published.
  assert.doesNotMatch(sec,/\d\s?(?:MiB|MB|GiB|GB)\b|RSS/,label+': no memory figure');
  // The next-day experiment: named, its design stated, no figure.
  const next=sec.slice(sec.indexOf('id="next-day"'),sec.indexOf('</p>',sec.indexOf('id="next-day"')));
  assert.ok(next.length>200,label+': the next-day status renders');
  assert.doesNotMatch(next,/\d+(?:\.\d+)?\s?%|\d\.\d|pp\b/,label+': the next-day experiment carries no figure');
  assert.match(next,label==='en'?/no figure from it is published/:/不发布它的任何数字/,label+': the next-day status says why');
  // The eTRCA filter-bank wording, corrected.
  assert.doesNotMatch(html,/three-filter-bank|三子带/,label+': the corrected eTRCA wording');
  assert.match(html,/href="\/data\/adaptation-update\.json"/,label+': the reviewed export is linked');
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
// The API page's Python example must run: pandas' URL reader is refused by the CDN.
for(const p of ['api/','zh/api/']){
  const html=pageOf(p);
  assert.doesNotMatch(html,/pd\.read_csv\(&quot;https?:|pd\.read_csv\("https?:/,p+': pandas must not open a URL itself');
  assert.match(html,/io\.StringIO/,p+': the example fetches with requests');
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

console.log('PASS: dataset, method and API pages — every figure re-read from its served file, bilingual parity, Markdown copies carry every figure, llms.txt complete, IndexNow key, no held source anywhere.');
console.log('PASS: short answers — question as h1 and title, every answer figure shown in the evidence below it, FAQPage equal to the printed answer.');
console.log('PASS: coverage matrix, eight topic pages, track changes, family filtering, sorting, empty state, dialogs, invalid inputs, export counts and English-only data.');
console.log('PASS: Chinese pages — lang, reciprocal hreflang, self canonical, every figure equal to English, credits kept, CSP, payload untranslated.');
console.log('PASS: 2026-10-01 adaptation — arm, contrast, seed and cost figures equal the audited export; matrix readout beside the head-only arm; no winner between LoRA and last block; next-day status figure-free; corrections listed; API example runs; no stage label.');
console.log('PASS: 2026-09-27 context — PC/VR, gait and non-control figures equal the audited export; no same-display claim; comparator beside gait; coverage beside conditional accuracy; no held source named.');
console.log('PASS: 2026-09-27 when not to act — idle figures from the reviewed protocol, roadmap proposal-only and figure-free; releases list every served file with its true SHA-256.');
console.log('PASS: 2026-09-23 clinical — comparator marked, claim boundary stated, demographics and withheld descriptors absent, holds carry no figures.');
console.log('PASS: 2026-09-22 evidence — Alpha Waves released with credits, no per-person values, R² unclamped, roadmap stays planned.');
console.log('Mocked WebMCP contract passed. Real supported-browser WebMCP integration has not been verified.');
