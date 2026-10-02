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
assert.match(built,/separate from the deployment topics above/,'homepage must distinguish the topic extension from the 39-comparison matrix');
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
// The masthead is styled through .site-header. A bare `header{` rule made the
// date row of every release entry a second sticky bar painted over the site
// navigation; a bare `nav{` laid the topic switcher out sideways.
for(const css of readdirSync(new URL(DIST+'_astro/',import.meta.url)).filter(f=>f.endsWith('.css')))
  assert.doesNotMatch(readFileSync(new URL(DIST+'_astro/'+css,import.meta.url),'utf8'),/(?:^|[{},])\s*(?:header|nav)\s*\{/,
    css+': a bare header or nav rule styles every <header> and <nav>, not only the masthead');
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
const zhTitles={'dry-vs-wet':'干电极的解码效果能和湿电极一样好吗？','fewer-electrodes':'更少的电极、或耳道内电极，能比得上完整的头皮电极吗？','screen-to-vr':'在屏幕上校准的 P300 解码器，换到 VR 里还管用吗？','on-the-move':'走路或跑步时，EEG 解码还管用吗？','clinical-groups':'静息态 EEG 能把帕金森病患者和对照组区分开吗？','calibration-budget':'可穿戴 SSVEP 解码器需要多少校准数据？','when-not-to-act':'没有人下指令时，EEG 解码器误触发有多频繁？','does-pretraining-help':'预训练对 LaBraM、CBraMod 这类 EEG 基础模型有帮助吗？'};
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
// The release log is checked here too; the API page is checked with the entity pages below.
for(const path of [...bilingual,'releases/']){
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
// The released medical disclaimer, the most safety-relevant sentence on the
// page, is in Chinese on the Chinese page, with the released English beside it.
{
  const zh=pageOf('zh/topics/clinical-groups/');
  assert.ok(zh.includes('<p class="protocol-note">公开数据集上的研究结果：不是诊断，不是诊断准确率，也不是医疗器械或医疗建议。'),'zh: the medical disclaimer must be in Chinese');
  assert.ok(zh.includes('<span lang="en">'+cl.medical_disclaimer+'</span>'),'zh: the released English disclaimer stays beside it, marked English');
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
const manifests=['publication_review_20260922/evidence-release-manifest.json','publication_review_20260923/clinical-release-manifest.json','publication_review_20260927/context-release-manifest.json',
  'publication_review_20261001/adaptation-release-manifest.json','publication_review_20261002/extension-release-manifest.json']
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
  auc3:r=>r.toFixed(3),auc2:r=>r.toFixed(2),num3:r=>r.toFixed(3).replace(/^-/,'−'),count:r=>r.toLocaleString('en-US'),s1:r=>r.toFixed(1)+' s'};
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

// --- Protocol pages (2026-10-02) -------------------------------------------------
// Each core-matrix protocol has its own address in both languages, built from the
// released track. Seven of the eight were reachable only through JavaScript. Their
// figures are re-read above from the protocol's own results CSV and protocol JSON;
// what is checked here is that nothing is missing and that the caveats travel.
{
  const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const figsOf=html=>[...html.matchAll(/data-fig="([^"]+)"[^>]*>([^<]*)</g)].map(m=>m[1]+' → '+m[2]);
  const allNames=[...new Set(data.tracks.flatMap(t=>t.rows.map(r=>r.name)))];
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
  for(const t of data.tracks){
    const path='protocols/'+t.id+'/', csv=t.id+'-results.csv', pj=t.id+'-protocol.json';
    for(const p of [path,'zh/'+path]) assert.ok(existsSync(new URL(p+'index.html',DIST)),p+': protocol page missing');
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
      assert.deepEqual([...new Set([...html.matchAll(/data-fig="([^|"]+)\|/g)].map(m=>m[1]))].sort(),[csv,pj].sort(),where+': figures must cite this protocol\'s CSV and JSON');
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
                         t.attribution,t.rightsScope,t.privacyReview,t.protocolId,t.version,t.license,...t.protocol,...(t.seedSensitivity?[t.seedSensitivity.scope]:[])])
        assert.ok(html.includes(esc(text)),where+': payload text missing: '+String(text).slice(0,60));
      if(t.seedSensitivity) for(const v of [...t.seedSensitivity.balancedAccuracyPercent,t.seedSensitivity.meanPercent])
        assert.ok(html.includes(`data-fig="${pj}|pct2raw|${v}"`),where+': seed result '+v);
      assert.ok(html.includes(`href="/data/${csv}"`)&&html.includes(`href="/data/${pj}"`),where+': both protocol downloads are linked');
      for(const [,href] of html.matchAll(/href="(\/[^"#]*)/g)) assert.ok(resolves(href),where+': link '+href+' does not resolve');
      // The released status field still reads "Research preview"; the site-wide check above keeps it off the page.
    }
    // Dataset markup, on the English page only: this protocol's CSV and JSON, part of the core matrix.
    const ld=JSON.parse(en.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
    assert.equal(ld['@type'],'Dataset',path+': Dataset markup');
    assert.deepEqual(ld.distribution.map(d=>d.contentUrl).sort(),[`https://bci.report/data/${csv}`,`https://bci.report/data/${pj}`].sort(),path+': distribution is the protocol\'s CSV and JSON');
    assert.equal(ld.url,'https://bci.report/'+path,path+': markup url');
    assert.equal(ld.isPartOf.url,'https://bci.report/',path+': part of the core-matrix Dataset');
    assert.ok(ld.variableMeasured.includes(t.yLabel)&&ld.variableMeasured.includes(t.xLabel),path+': both metrics');
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

console.log('PASS: protocol pages — both languages, every method with a score, every figure re-read from the protocol\'s own CSV and JSON, chance levels and the blank-cell caveat, payload text verbatim, Dataset markup, links resolve; entity groups and matrix headings lead here.');

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
    for(const [bad,good] of Object.entries(rejected)) assert.ok(!zh.includes(bad),`directory-zh.json: "${bad}" is a rejected rendering — use "${good}"`);
  }
  // Licence names are names: one spelling in every language.
  const licenceName=/^(?:MIT|GPL-3\.0|CC0-1\.0|CC BY 4\.0|CC BY-ND 4\.0|CC BY-NC-ND 4\.0|Open Data Commons Attribution License 1\.0)$/;
  const texts=[...data.models.flatMap(m=>[m.note,m.license]),...data.datasets.flatMap(d=>[d.detail,d.license])];
  for(const text of texts) assert.ok(dirZh[text]||licenceName.test(text),'directory-zh.json: no Chinese for "'+text.slice(0,60)+'"');
  for(const key of Object.keys(dirZh)) assert.ok(texts.includes(key),'directory-zh.json: "'+key.slice(0,50)+'" matches no text in mvp.json');
  const zhHome=read('zh/');
  const directory=zhHome.slice(zhHome.indexOf('id="models"'),zhHome.indexOf('id="news"'));
  assert.ok(directory.length>2000,'zh: the model directory and data register must render');
  assert.doesNotMatch(directory,/<p lang="en">/,'zh: model notes and rights-review notes are printed in Chinese');
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
  assert.deepEqual([...umbrella.sameAs].sort(),[mirror,repository].sort(),'home Dataset sameAs: the mirror and the repository');
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
    assert.ok(feed.includes(`SHA-256 &lt;code&gt;${createHash('sha256').update(bytes).digest('hex')}&lt;/code&gt;`),'releases.xml: '+file+' must carry the SHA-256 of the served bytes');
  }
  for(const f of htmlPages){
    const html=readFileSync(new URL(f,DIST),'utf8');
    assert.ok(html.includes('<link rel="alternate" type="application/atom+xml" title="BCI Report releases" href="/releases.xml">'),f+': the release feed must be linked in <head>');
  }
  for(const p of ['api/','zh/api/']){
    const html=pageOf(p);
    for(const href of ['/releases.xml','/llms-full.txt','/llms.txt','/sitemap.xml']) assert.ok(html.includes(`href="${href}"`),p+': '+href+' must be linked for agents');
    for(const href of [repository,mirror,citationFile]) assert.ok(html.includes(`href="${href}"`),p+': '+href+' must be linked');
    // The CDN still refuses urllib: the edge setting has not changed, so the caveat stays.
    assert.match(html,p==='api/'?/The CDN refuses Python’s built-in urllib/:/CDN 会拒绝 Python 自带的 urllib/,p+': the urllib caveat must stay until the edge stops refusing it');
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
// files hold its figures (topic pages: the downloads they link; entity pages: the
// files their data-fig figures are leaves of). citation_* tags carry the same.
{
  const citePages=[...topicPages.map(([s])=>'topics/'+s+'/'),...entityBilingual.filter(p=>/^(?:datasets|methods)\/[^/]+\/$/.test(p))];
  assert.ok(citePages.length>=8+16+9,'cite blocks on every topic, dataset and method page');
  for(const p of citePages) for(const path of [p,'zh/'+p]){
    const html=pageOf(path),zh=path.startsWith('zh/');
    const start=html.indexOf('<section class="cite-page"');
    assert.ok(start>0,path+': the cite block must render');
    const sec=html.slice(start,html.indexOf('</section>',start));
    const named=sec.match(/data-releases="([^"]+)"/)[1].split(' ');
    const files=p.startsWith('topics/')?[...html.matchAll(/href="\/data\/([^"]+)"/g)].map(m=>m[1]):[...html.matchAll(/data-fig="([^|"]+)\|/g)].map(m=>m[1]);
    const expected=releaseEntries.filter(r=>files.some(f=>releaseOf.get(f)===r)).map(r=>r.id);
    assert.deepEqual(named,expected,path+': the cite block must name exactly the releases its figures come from, newest first');
    for(const id of named) assert.ok(sec.includes(`href="${zh?'/zh':''}/releases/#${id}"><code>${id}</code></a>`),path+': '+id+' must link to its release');
    // The h1 may carry markup (an English name in <span lang="en">, <wbr> phrase breaks); the cite block names its text.
    const h1=html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/)[1].replace(/<[^>]+>/g,''),canonical='https://bci.report/'+path;
    assert.ok(sec.includes(`<cite>${h1}</cite>`)&&sec.includes(`<span class="cite-url">${canonical}</span>`),path+': the cite block names the page and its address');
    assert.match(sec,zh?/也请同时引用上游数据集/:/Cite the upstream datasets? as well/,path+': the cite block sends the reader to the upstream credit');
    const newest=releaseEntries.find(r=>r.id===named[0]);
    const meta=k=>decodeHtml(html.match(new RegExp(`<meta name="citation_${k}" content="([^"]*)">`))?.[1]??'');
    assert.equal(meta('title'),decodeHtml(h1),path+': citation_title is the h1');
    assert.equal(meta('author'),'BCI Report',path+': citation_author');
    assert.equal(meta('publication_date'),newest.date.replaceAll('-','/'),path+': citation_publication_date is the newest cited release');
    assert.equal(meta('public_url'),canonical,path+': citation_public_url is the canonical');
    const md=readFileSync(new URL(path+'index.md',DIST),'utf8');
    assert.ok(md.includes(zh?'## 引用本页':'## Cite this page')&&named.every(id=>md.includes('`'+id+'`'))&&md.includes(canonical),path+': the cite block must survive into the Markdown copy');
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
}

console.log('PASS: 2026-10-02 discoverability — share card is the recorded badge-free bitmap with alt/size on every page; home Dataset cites the newest release with every file and topic part; Atom feed matches the release log; only /data/* is cross-origin; cite blocks name exactly their releases, in both languages and Markdown; table names survive into Markdown; footers, llms.txt, licences and .zenodo.json agree.');
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
