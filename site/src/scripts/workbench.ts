import data from '../data/mvp.json';
type Track=typeof data.tracks[number];
type Row=Track['rows'][number];
const $=<T extends HTMLElement=HTMLElement>(s:string)=>document.querySelector<T>(s)!;
const esc=(s:unknown)=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
let track:Track=data.tracks[0];
/* Warm series, deliberately with no blue in it: slate blue is reserved for the
   chance reference line, which must never read as one more model. Neighbours
   differ in lightness as well as hue (the fifth was a second rust, the sixth an
   olive that a deuteranope sees as the teal), and the legend is numbered, so
   the colour is never the only link between a mark and its name. Kept in step
   with the .legend i.sN swatches in generated.css. */
const colors=['#b3450e','#1f6f63','#8a6d1f','#7a4a8c','#3b3029','#b5487a','#5c7a2e','#6b3f5e'];
const CHANCE_LINE='#2f5f74';
const pct=(v:number)=>v.toFixed(1)+'%';

/* Interface strings this script generates. It cannot import src/data/i18n.ts:
   check-workbench.mjs runs it in a vm with only its `import data` line removed,
   so the table lives here. Protocol titles are NOT duplicated — they are read
   back from the server-rendered tab buttons, which i18n.ts already localised.
   The page's <html lang> picks the table; anything else (including the test's
   DOM double, which has no documentElement) falls back to English. */
const LANG=((document as Document & {documentElement?:{lang?:string}}).documentElement?.lang??'').startsWith('zh')?'zh':'en';
/* Release prose stays English on the Chinese page. The server marks it
   lang="en"; render() replaces that markup, so it has to mark it again, or a
   screen reader reads English in a Chinese voice after the first paint. */
const EN=LANG==='zh'?' lang="en"':'';
const S={
  en:{subjects:' subjects',rights:'Aggregate research results',secondaryUp:'Secondary metric ↑',secondaryDown:'Secondary metric ↓',
      empty:'No evaluated models from this family in this track. Try another family.',noResults:'No results to display',
      licence:'Licence: ',licenceLink:'Licence ↗',
      tradeoffTitle:'Detection meets reliability',accuracyTitle:'Accuracy by configuration',
      tradeoffNote:'Upper left is better. Always abstaining also yields zero false activations, so detection must be read alongside them.',
      accuracyNote:'Subject-mean balanced accuracy. Error bars show descriptive 95% intervals where available.',
      chanceLine:(c:number)=>' The dashed line marks the '+c+'% chance level for this task.',chanceSee:' See the protocol for chance level.',
      chartLabel:(y:string,x:string)=>y+' and '+x+' chart',tip:(n:string,v:string)=>n+': '+v,
      tipTradeoff:(n:string,d:string,f:string)=>n+': detection '+d+', false activation '+f,
      axisFa:'Idle false activation rate →',axisDetect:'Command detection % ↑',axisBa:'Balanced accuracy % ↑',axisOrder:'Configurations follow legend order',
      atOrBelow:(c:number)=>'At or below the '+c+'% chance level',reaches:(c:number)=>'Interval reaches the '+c+'% chance level',
      seed:(w:string,n:number,lo:string,hi:string,m:string)=>'Single seed — the '+w+' of '+n+' run ('+lo+'–'+hi+'%, mean '+m+'%)',
      seedWord:{highest:'highest',lowest:'lowest',middle:'middle'} as Record<string,string>,
      abstained:(a:number,n:number)=>a+' of '+n+' participants always abstained',
      scopeTail:(w:string)=>' On this metric the retained seed is also the '+w+' of the three; the seed was fixed and audited before the other two were run.',
      protocol:' · Protocol',stageSum:'Scoring stage sum',seconds:' seconds',accel:' · may include accelerator waiting',stability:'Configuration stability',
      release:'Dataset release: ',protocolId:'Protocol: ',audit:'Audit record SHA256: ',scope:'Source and permitted scope',
      dlProtocol:'Download protocol · JSON ↓',original:'Original dataset ↗',participants:' participants',
      abstainNote:(n:number,a:number)=>'Of '+n+' participants, '+a+' selected an always-abstain threshold on calibration data. Their test trials remain in the denominator.',
      cohortOnly:'Only cohort aggregates are shared. Individual scores, recordings and predictions remain local.',
      privacy:'Privacy',privacyNote:'Only cohort aggregates are published here: no recording, no participant identifier, no per-person score.',
      privacyLink:'The full review note is in the protocol JSON ↓',register:'Public-data register note',
      consentCaveat:{'sleep-scalp':'According to the 2025 data descriptor, the informed consent form did not mention publication, and before release the GDPR office of Region Midt judged the data fully anonymised: consent covered the study, and the public release rests on that anonymisation judgement.'} as Record<string,string>,
      metric:{} as Record<string,string>,
      fmGroup:(n:number,date:string,notRun=0)=>'Added '+date+': '+n+' further foundation encoders, frozen (v9)'+(notRun?' · '+notRun+' not run on this protocol':''),fmGroupLink:'Every v9 row with its footnote →',
      fmInterval:(lo:string,hi:string)=>'Descriptive 95% interval: '+lo+'–'+hi+'%',fmF1:'Mean across held-out participants',
      fmDetected:(d:number,n:number)=>d+' of '+n+' commands',fmIdle:(f:number,n:number)=>f+' of '+n+' idle trials',
      fmNotRun:'Not run',fmNotPublished:'not published',fmExposed:'In the authors’ pretraining list',fmUnknown:'Exposure unknown',
      fmResearchUse:'Model card: research use only, not for diagnosis or clinical use.',
      fmAblationReference:'matrix row above',fmSource:'source ↗',fmMethod:'Model page →',fmCsv:'v9 rows · CSV ↓',
      fmExposureLabel:'Pretraining exposure: ',fmFootnote:'Row footnote: ',fmLicence:'Weights licence: ',
      fmFrozen:'Frozen probe added 2026-10-04 (release v9): the published recipe with only the encoder swapped. Grouped by family, never ranked.',
      stop:'. ',coreExposureLead:'Checked 2026-10-04 — LaBraM and CBraMod: ',coreExposureTail:'That is what the authors’ lists show, not proof that these recordings were never seen; the sentence above is the released one, which predates the check.'},
  zh:{subjects:' 名被试',rights:'聚合研究结果',secondaryUp:'次指标 ↑',secondaryDown:'次指标 ↓',
      empty:'该协议下没有这一类别的已评测模型。请换一个类别。',noResults:'无可显示的结果',
      licence:'许可：',licenceLink:'许可 ↗',
      tradeoffTitle:'检出率与可靠性',accuracyTitle:'各配置的准确率',
      tradeoffNote:'越靠左上越好。始终拒识也能得到零误触发，所以检出率必须和误触发率一起读。',
      accuracyNote:'被试平均平衡准确率。误差线在有数据时表示描述性 95% 区间。',
      chanceLine:(c:number)=>'虚线标出本任务 '+c+'% 的随机水平。',chanceSee:'随机水平见协议说明。',
      chartLabel:(y:string,x:string)=>y+'与'+x+'图',tip:(n:string,v:string)=>n+'：'+v,
      tipTradeoff:(n:string,d:string,f:string)=>n+'：检出率 '+d+'，误触发率 '+f,
      axisFa:'空闲误触发率 →',axisDetect:'指令检出率 % ↑',axisBa:'平衡准确率 % ↑',axisOrder:'配置按图例顺序排列',
      atOrBelow:(c:number)=>'不高于 '+c+'% 随机水平',reaches:(c:number)=>'区间触及 '+c+'% 随机水平',
      seed:(w:string,n:number,lo:string,hi:string,m:string)=>'仅单个随机种子——为 '+n+' 次运行中'+w+'（'+lo+'–'+hi+'%，均值 '+m+'%）',
      seedWord:{highest:'最高的一次',lowest:'最低的一次',middle:'居中的一次'} as Record<string,string>,
      abstained:(a:number,n:number)=>n+' 名被试中有 '+a+' 名始终拒识',
      scopeTail:(w:string)=>' 在这个指标上，保留的种子也是三次中'+w+'；该种子在另外两次运行之前就已固定并审计。',
      protocol:' · 协议',stageSum:'评分阶段总耗时',seconds:' 秒',accel:' · 可能含加速器等待',stability:'配置稳定性',
      release:'数据集版本：',protocolId:'协议：',audit:'审计记录 SHA256：',scope:'来源与许可范围',
      dlProtocol:'下载协议 · JSON ↓',original:'原始数据集 ↗',participants:' 名被试',
      abstainNote:(n:number,a:number)=>n+' 名被试中，有 '+a+' 名在校准数据上选择了始终拒识的阈值。他们的测试试次仍计入分母。',
      cohortOnly:'只公开队列级聚合结果。个体分数、记录与预测均保留在本地。',
      privacy:'隐私',privacyNote:'这里只发布队列级聚合结果：不发布任何记录、被试编号或逐人分数。',
      privacyLink:'完整的审查说明在协议 JSON 中 ↓',register:'公开数据登记说明',
      consentCaveat:{'sleep-scalp':'据 2025 年的数据描述论文，知情同意书没有提到公开发布；发布前，Region Midt（丹麦中部大区）的 GDPR 办公室判定这些数据已完全匿名化：同意书覆盖的是研究本身，公开发布依据的是这一匿名化判定。'} as Record<string,string>,
      metric:{'Balanced accuracy':'平衡准确率','Command detection ≤3s':'指令检出率 ≤3 秒','Idle false activation':'空闲误触发率','Macro F1':'宏平均 F1'} as Record<string,string>,
      fmGroup:(n:number,date:string,notRun=0)=>date+' 新增：另外 '+n+' 个基础模型编码器（冻结，第九轮）'+(notRun?'，其中 '+notRun+' 个在这个协议上未运行':''),fmGroupLink:'第九轮的每一行及其脚注 →',
      fmInterval:(lo:string,hi:string)=>'描述性 95% 区间：'+lo+'–'+hi+'%',fmF1:'各留出被试的均值',
      fmDetected:(d:number,n:number)=>'检出 '+d+' / '+n+' 条指令',fmIdle:(f:number,n:number)=>'误触发 '+f+' / '+n+' 个空闲试次',
      fmNotRun:'未运行',fmNotPublished:'不发布',fmExposed:'在作者的预训练清单中',fmUnknown:'是否出现在预训练数据中：未知',
      fmResearchUse:'模型卡：仅供研究使用，不可用于诊断或临床。',
      fmAblationReference:'即上表中的那一行',fmSource:'来源 ↗',fmMethod:'模型页面 →',fmCsv:'第九轮各行 · CSV ↓',
      fmExposureLabel:'是否出现在预训练数据中：',fmFootnote:'该行脚注：',fmLicence:'权重许可：',
      fmFrozen:'2026-10-04 新增的冻结探针（第九轮发布）：沿用已发布的方案，只替换编码器。按模型类别分组，从不排名。',
      stop:'。',coreExposureLead:'2026-10-04 核查——LaBraM 与 CBraMod：',coreExposureTail:'这是作者清单所显示的情况，并不证明这些记录从未被模型见过；上面那句话是发布时的原文，早于这次核查。'},
}[LANG];
const metric=(label:string)=>S.metric[label]??label;
/* The v9 foundation-model rows (2026-10-04). The page embeds them as JSON
   (#fm-rows, written by index.astro from the served per-protocol CSVs, with the
   prose already in the page's language), so this script needs no second import
   and check-workbench.mjs can hand its DOM double the same JSON it reads from
   dist/. They are stacked under the core rows, never merged into mvp.json:
   their own group, sorted within it, with the chance flags the core rows carry
   and the owner's sourced pretraining-exposure statement. */
type FmRow={id:string;name:string;panel:string;href:string;mode:string;channels:number;subjects:number|null;y:number|null;interval:[number,number]|null;
  x:number|null;chanceFlag:'at-or-below'|'interval-reaches'|null;status:string;reason:string|null;reasonOriginal:string|null;exposure:string;exposureText:string;exposureSource:string|null;
  footnote:string;footnoteOriginal:string|null;notes:string;licence:string;licenceOriginal:string|null;researchUse:boolean;
  idle:{detected:number;commandTrials:number;falseActivations:number;idleTrials:number;abstain:number}|null};
type FmData={release:string;date:string;tracks:Record<string,{file:string;protocolHref:string;rows:FmRow[];coreExposure?:{text:string;urls:string[]}}>};
const fmData:FmData=(()=>{try{return JSON.parse(document.querySelector('#fm-rows')?.textContent||'');}catch{return {release:'',date:'',tracks:{}};}})();
const fmOf=(id:string)=>fmData.tracks[id]??{file:'',protocolHref:'',rows:[]};
/* Two tracks carry a JSON fragment in their release text ('… v3 · {"mirror": …,
   "upstream": …}'). Printed as its fields, "mirror … · upstream …", as the
   protocol pages print it (versionText in src/data/protocols.ts). */
const versionText=(v:string)=>v.replace(/\{[^{}]*\}/g,f=>{try{return Object.entries(JSON.parse(f) as Record<string,unknown>).map(([k,x])=>k+' '+String(x)).join(' · ');}catch{return f;}});
const xValue=(r:Row)=>track.type==='tradeoff'?pct(r.x):r.x.toFixed(3);

/** Seed-sensitivity record, present on the two tracks that were re-run. */
type SeedSensitivity={model:string;seeds:number[];balancedAccuracyPercent:number[];meanPercent:number;sampleSdPercentagePoints:number};
const seedInfo=(t:Track)=>(t as Partial<{seedSensitivity:SeedSensitivity}>).seedSensitivity;

/** Where the displayed (original-seed) value sits among the seeds actually run. */
function seedRank(ss:SeedSensitivity){
  const v=ss.balancedAccuracyPercent,shown=v[0],hi=Math.max(...v),lo=Math.min(...v);
  const key=shown>=hi?'highest':shown<=lo?'lowest':'middle';
  return {shown,hi,lo,word:S.seedWord[key]};
}

/* The headline number on these rows is one seed. Saying so only inside the
   protocol dialog left the table looking like a settled measurement, so the
   condition travels with the number instead. */
function seedFlag(r:Row){
  const ss=seedInfo(track);
  if(!ss||ss.model!==r.name)return '';
  const {hi,lo,word}=seedRank(ss);
  return '<span class="flag seed">'+S.seed(word,ss.balancedAccuracyPercent.length,lo.toFixed(2),hi.toFixed(2),ss.meanPercent.toFixed(2))+'</span>';
}

/* A zero false-activation rate produced by participants who always abstain is
   not reliability. The count was only in the model dialog; it belongs next to
   the 0.0% a reader is scanning. */
function abstainFlag(r:Row){
  if(track.type!=='tradeoff'||!r.abstain)return '';
  return '<span class="flag">'+S.abstained(r.abstain,r.subjects)+'</span>';
}

/* `scope` already carries the clearest statement of why the retained seed is the
   retained one. It was sitting unused in the data while the weaker sentence was
   the only thing shown, which is the reverse of what a sceptical reader needs —
   on both seed-tested tracks the retained value is also the highest of the three. */
function seedScopeNote(){
  const ss=seedInfo(track) as (SeedSensitivity&{scope?:string})|undefined;
  if(!ss)return '';
  const {word}=seedRank(ss);
  return '<p class="detail-note"><span'+EN+'>'+esc(ss.scope??'')+'</span>'+S.scopeTail(word)+'</p>';
}

/* The released privacy review reads as the reviewer's working notes, so the
   dialog treats it as the protocol pages (/protocols/<id>/) do: one site-written
   sentence, any consent caveat, the public-data register's reviewed rights note
   for the dataset, and a link to the protocol JSON, which holds the full note.
   The strings are the pages' own (protocolCopy in src/data/entity-copy.ts);
   check-workbench.mjs compares the two. The register note prints in English on
   both pages, marked lang="en" on the Chinese one: its Chinese is in
   src/data/directory-zh.json, which this script does not read. */
function privacyNote(){
  const note=data.datasets.find(d=>d.name===track.dataset)?.detail;
  const caveat=S.consentCaveat[track.id];
  return '<p class="protocol-privacy"><strong>'+S.privacy+'</strong> '+S.privacyNote+(caveat?' <span class="consent-caveat">'+caveat+'</span>':'')+' <a href="/data/'+track.id+'-protocol.json" download>'+S.privacyLink+'</a></p>'+
    (note?'<p class="protocol-register"><strong>'+S.register+'</strong> <span'+EN+'>'+esc(note)+'</span></p>':'');
}

const chanceOf=(t:Track)=>(t as Partial<{chanceLevel:number|null}>).chanceLevel ?? null;

/* Several rows sit at or below chance once their interval is taken into
   account. Chance was only ever stated inside the protocol, so a 49.4% on a
   50%-chance task read like an ordinary score. */
function chanceFlag(r:Row){
  const c=chanceOf(track);
  if(c===null||track.type==='tradeoff')return '';
  const iv=(r as Partial<{interval:number[]|null}>).interval;
  if(r.y<=c)return '<span class="flag">'+S.atOrBelow(c)+'</span>';
  if(iv&&iv[0]<=c)return '<span class="flag">'+S.reaches(c)+'</span>';
  return '';
}
/* All eight protocols are listed as tabs rather than hidden in a <select>, so
   the shape of the release is visible before anything is chosen. Roving
   tabindex keeps the group a single stop in the tab order. */
const tabs=[...document.querySelectorAll<HTMLElement>('.track-tab')];
/** The protocol title as the page rendered it, so the locale's title has one source. */
const titleOf=(t:Track)=>tabs.find(b=>b.dataset.track===t.id)?.querySelector('strong')?.textContent||t.title;
function syncTabs(){
  $('#track-tabs').setAttribute('data-active',track.id);
  $('#track-panel').setAttribute('aria-labelledby','tab-'+track.id);
  for(const b of tabs){const on=b.dataset.track===track.id;b.setAttribute('aria-selected',on?'true':'false');b.tabIndex=on?0:-1;}
}

const dialog=$<HTMLDialogElement>('#detail-dialog');
function show(title:string,body:string){$('#dialog-title').textContent=title;$('#dialog-body').innerHTML=body;dialog.showModal();}
function visibleRows(){const f=$<HTMLSelectElement>('#family-filter').value,s=$<HTMLSelectElement>('#sort-results').value;return track.rows.filter(r=>f==='all'||r.family===f).slice().sort((a,b)=>s==='y-desc'?b.y-a.y:s==='x-asc'?(track.type==='tradeoff'?a.x-b.x:b.x-a.x):a.name.localeCompare(b.name));}
/* The v9 rows of this protocol, in their own group: the family filter applies
   (they are foundation models), and a sort orders them within the group only,
   never in among the released rows. A cell not run has no number and sorts last. */
function visibleFm(panel='matrix'){const f=$<HTMLSelectElement>('#family-filter').value,s=$<HTMLSelectElement>('#sort-results').value;
  if(f!=='all'&&f!=='foundation')return [];
  const last=(v:number|null)=>v===null?1:0;
  return fmOf(track.id).rows.filter(r=>r.panel===panel).slice().sort((a,b)=>s==='y-desc'?last(a.y)-last(b.y)||(b.y??0)-(a.y??0)
    :s==='x-asc'?last(a.x)-last(b.x)||(track.type==='tradeoff'?(a.x??0)-(b.x??0):(b.x??0)-(a.x??0)):a.name.localeCompare(b.name));}
/* The flag the protocol page prints, computed there from the CSV's full values (the
   embedded figures are rounded to what the table shows): the same wording as the core rows. */
function fmChance(r:FmRow){
  const c=chanceOf(track);
  if(c===null||track.type==='tradeoff'||!r.chanceFlag)return '';
  return '<span class="flag">'+(r.chanceFlag==='at-or-below'?S.atOrBelow(c):S.reaches(c))+'</span>';
}
const fmBadge=(r:FmRow)=>r.exposure==='exposed'?'<span class="flag fm-badge" data-exposure="exposed">'+S.fmExposed+'</span>'
  :r.exposure==='unknown'?'<span class="flag fm-badge" data-exposure="unknown">'+S.fmUnknown+'</span>':'';
function fmRowHtml(r:FmRow,reference=false){
  const tradeoff=track.type==='tradeoff',i=r.idle;
  const name='<td><button class="model-name" data-model="fm:'+esc(r.id)+'">'+esc(r.name)+' ↗</button><small'+EN+'>'+esc(r.mode)+' · '+r.channels+' ch</small>'+
    (reference?'<small>'+S.fmAblationReference+'</small>':'')+(r.researchUse?'<small class="fm-research-use">'+S.fmResearchUse+'</small>':'')+'</td>';
  const cells=r.status!=='complete'||r.y===null||r.x===null
    ?'<td colspan="2" class="fm-not-run"><strong>'+S.fmNotRun+'</strong><small>'+esc(r.reason??'')+'</small>'+fmBadge(r)+'</td>'
    :tradeoff&&i
      ?'<td><strong>'+pct(r.y)+'</strong><small>'+S.fmDetected(i.detected,i.commandTrials)+'</small>'+(i.abstain?'<span class="flag">'+S.abstained(i.abstain,r.subjects??0)+'</span>':'')+fmBadge(r)+'</td>'+
       '<td><strong>'+pct(r.x)+'</strong><small>'+S.fmIdle(i.falseActivations,i.idleTrials)+'</small></td>'
      :'<td><strong>'+pct(r.y)+'</strong><small>'+(r.interval?S.fmInterval(r.interval[0].toFixed(1),r.interval[1].toFixed(1)):'')+'</small>'+fmChance(r)+fmBadge(r)+'</td>'+
       '<td><strong>'+r.x.toFixed(3)+'</strong><small>'+S.fmF1+'</small></td>';
  return '<tr class="fm-row" data-fm="'+esc(r.id)+'">'+name+cells+'<td><small>'+S.fmNotPublished+'</small></td></tr>';
}
function fmGroupHtml(fm:FmRow[]){
  if(!fm.length)return '';
  const t=fmOf(track.id);
  return '<tr class="fm-group"><th colspan="4" scope="colgroup">'+esc(S.fmGroup(fm.length,fmData.date,fm.filter(r=>r.status!=='complete').length))+' <a href="'+esc(t.protocolHref)+'#foundation-v9">'+S.fmGroupLink+'</a></th></tr>'+fm.map(r=>fmRowHtml(r)).join('');
}
function ablationHtml(){
  const ref=visibleFm().filter(r=>r.id.startsWith('eeg-fm-masking/')),sib=visibleFm('masking ablation');
  return ref.map(r=>fmRowHtml(r,true)).join('')+sib.map(r=>fmRowHtml(r)).join('');
}
function render(){
const rows=visibleRows();
$('#track-title').textContent=track.subtitle;
$('#track-meta').innerHTML=esc(track.dataset)+' · '+track.subjects+S.subjects+' · <span'+EN+'>'+esc(track.observations)+' · '+esc(track.exposure)+'</span>';
$('#track-limitation').textContent=track.limitation;
$('#track-rights').innerHTML='<span'+EN+'>'+esc(track.license)+'</span> · '+S.rights;
$<HTMLAnchorElement>('#track-source').href=track.source;
syncTabs();
$('#secondary-sort').textContent=track.type==='tradeoff'?S.secondaryUp:S.secondaryDown;
$('#metric-y-heading').textContent=metric(track.yLabel);$('#metric-x-heading').textContent=metric(track.xLabel);
$<HTMLAnchorElement>('#download-results').href='/data/'+track.id+'-results.csv';
const fm=visibleFm();
$('#result-rows').innerHTML=rows.length||fm.length?rows.map(r=>'<tr><td><button class="model-name" data-model="'+esc(r.id)+'">'+esc(r.name)+' ↗</button><small'+EN+'>'+esc(r.mode)+' · '+r.channels+' ch</small></td><td><strong>'+pct(r.y)+'</strong><small'+EN+'>'+esc(r.yDetail)+'</small>'+chanceFlag(r)+seedFlag(r)+'</td><td><strong>'+xValue(r)+'</strong><small'+EN+'>'+esc(r.xDetail)+'</small>'+abstainFlag(r)+'</td><td>'+r.seconds.toFixed(1)+'s</td></tr>').join('')+fmGroupHtml(fm):'<tr><td colspan="4" class="empty">'+S.empty+'</td></tr>';
$('#ablation-rows').innerHTML=ablationHtml();
$<HTMLAnchorElement>('#download-fm').href='/data/'+fmOf(track.id).file;
draw([...rows.map(r=>({name:r.name,y:r.y,x:r.x,interval:(r as Partial<{interval:number[]|null}>).interval??null})),
      ...fm.filter(r=>r.y!==null&&r.x!==null).map(r=>({name:r.name,y:r.y as number,x:r.x as number,interval:r.interval}))],rows.length);
hint();
}
/* Only advertise horizontal scrolling when there is something to reach. */
function hint(){
const box=$('.table-panel .scroll'),el=$('#scroll-hint');
if(box.scrollWidth>box.clientWidth+1)el.setAttribute('data-overflow','');else el.removeAttribute('data-overflow');
}
window.addEventListener('resize',hint);
/* `rows` are the marks in table order: the released rows, then the v9 rows; `split`
   is where the v9 group starts. With more than ten bars the printed values move to
   the table and the tooltips, or the labels would overlap. */
type Mark={name:string;y:number;x:number;interval:number[]|null};
function draw(rows:Mark[],split=rows.length){
const tradeoff=track.type==='tradeoff';
$('#chart-title').textContent=tradeoff?S.tradeoffTitle:S.accuracyTitle;
const chanceNote=chanceOf(track);
$('#chart-note').textContent=tradeoff?S.tradeoffNote:S.accuracyNote+(chanceNote!==null?S.chanceLine(chanceNote):S.chanceSee);
// A class rather than style="background:…": the Content-Security-Policy in
// public/_headers allows no inline style at all, and an innerHTML-injected
// style attribute is blocked by it.
$('#chart-legend').innerHTML=rows.map((r,i)=>'<li><i class="s'+(i%colors.length)+'"></i><span class="n">'+(i+1)+'</span> '+esc(r.name)+'</li>').join('');
if(!rows.length){$('#result-chart').innerHTML='<p class="empty">'+S.noResults+'</p>';return;}
const x0=38,y0=176,w=210,h=145;
let svg='<svg viewBox="0 0 280 220" role="img" aria-label="'+esc(S.chartLabel(metric(track.yLabel),metric(track.xLabel)))+'">';
[0,25,50,75,100].forEach(v=>{const y=y0-h*v/100;svg+='<line x1="'+x0+'" x2="'+(x0+w)+'" y1="'+y+'" y2="'+y+'" stroke="#e7dccd"/><text x="29" y="'+(y+4)+'" text-anchor="end">'+v+'</text>';});
if(tradeoff){const maxX=Math.max(5,...rows.map(r=>r.x))*1.2;
[0,maxX/2,maxX].forEach(v=>{const x=x0+w*v/maxX;svg+='<text x="'+x+'" y="195" text-anchor="middle">'+v.toFixed(1)+'%</text>';});
rows.forEach((r,i)=>{const x=x0+w*r.x/maxX,y=y0-h*r.y/100;svg+='<circle cx="'+x+'" cy="'+y+'" r="5" fill="'+colors[i%colors.length]+'" stroke="#fffdfa" stroke-width="1.5"><title>'+esc(S.tipTradeoff(r.name,pct(r.y),pct(r.x)))+'</title></circle><text x="'+(x+8)+'" y="'+(y+4)+'">'+(i+1)+'</text>';});
svg+='<text x="145" y="216" text-anchor="middle">'+S.axisFa+'</text><text x="38" y="16">'+S.axisDetect+'</text>';
}else{const gap=w/rows.length,chance=chanceOf(track);
// Without this line a 10.8% on a 40-class task and a 49.4% on a 2-class task
// look equally unremarkable against 0/25/50/75/100 gridlines.
// Named in the note rather than on the line: at 2.5% chance the label would sit
// on top of the bars, and the note has room to say what the line means.
if(chance!==null){const cy=y0-h*chance/100;
svg+='<line x1="'+x0+'" x2="'+(x0+w)+'" y1="'+cy+'" y2="'+cy+'" stroke="'+CHANCE_LINE+'" stroke-width="1.2" stroke-dasharray="5 3"/>';}
const dense=rows.length>10;
if(split>0&&split<rows.length){const sx=x0+gap*split;svg+='<line class="fm-split" x1="'+sx+'" x2="'+sx+'" y1="'+(y0-h)+'" y2="'+y0+'" stroke="#9c8a76" stroke-width="1" stroke-dasharray="2 3"/>';}
rows.forEach((r,i)=>{const x=x0+gap*(i+.5),height=h*r.y/100;svg+='<rect x="'+(x-gap*.25)+'" y="'+(y0-height)+'" width="'+gap*.5+'" height="'+height+'" rx="2" fill="'+colors[i%colors.length]+'"><title>'+esc(S.tip(r.name,pct(r.y)))+'</title></rect>'+(dense?'':'<text x="'+x+'" y="'+(y0-height-7)+'" text-anchor="middle">'+r.y.toFixed(1)+'</text>')+'<text x="'+x+'" y="195" text-anchor="middle"'+(dense?' class="dense"':'')+'>'+(i+1)+'</text>';if(Array.isArray(r.interval)){const [a,b]=r.interval;const w=Math.min(4,gap*.25);svg+='<path d="M'+x+','+(y0-h*a/100)+'V'+(y0-h*b/100)+' M'+(x-w)+','+(y0-h*a/100)+'h'+(2*w)+' M'+(x-w)+','+(y0-h*b/100)+'h'+(2*w)+'" stroke="#241c15" stroke-width="1"/>';}});
svg+='<text x="38" y="16">'+S.axisBa+'</text><text x="145" y="216" text-anchor="middle">'+S.axisOrder+'</text>';
}$('#result-chart').innerHTML=svg+'</svg>';
}
// The panel is named by its tab (aria-labelledby, set in syncTabs); an
// aria-label beside it was ignored by every reader and only drifted.
function selectTrack(id:string){const found=data.tracks.find(t=>t.id===id);if(!found)throw new Error('Unknown track');track=found;render();}
$('#track-tabs').addEventListener('click',e=>{const b=(e.target as HTMLElement).closest<HTMLElement>('.track-tab');if(b?.dataset.track)selectTrack(b.dataset.track);});
$('#track-tabs').addEventListener('keydown',e=>{
  const key=(e as KeyboardEvent).key,at=tabs.findIndex(b=>b.dataset.track===track.id);
  const next=key==='ArrowRight'||key==='ArrowDown'?at+1:key==='ArrowLeft'||key==='ArrowUp'?at-1:key==='Home'?0:key==='End'?tabs.length-1:-1;
  if(next<0&&key!=='Home')return;
  e.preventDefault();
  const target=tabs[(next+tabs.length)%tabs.length];
  if(!target?.dataset.track)return;
  selectTrack(target.dataset.track);target.focus();
});
/* A column heading in the coverage matrix links to that protocol's own page
   (/protocols/<id>/), with or without JavaScript. The handler also switches the
   panel below to it, so a Back navigation restored from the page cache shows the
   protocol last opened. */
$('#overview').addEventListener('click',e=>{const a=(e.target as HTMLElement).closest<HTMLElement>('[data-jump]');if(a?.dataset.jump)selectTrack(a.dataset.jump);});
$('#family-filter').addEventListener('change',render);$('#sort-results').addEventListener('change',render);
$('#open-protocol').addEventListener('click',()=>show(titleOf(track)+S.protocol,
'<p'+EN+'>'+esc(track.subtitle)+'</p><ol'+EN+'>'+track.protocol.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol>'+
'<div class="detail-metrics"><div><small>'+S.stageSum+'</small><strong>'+track.elapsed.toFixed(1)+S.seconds+'</strong><small><span'+EN+'>'+esc(track.backend)+'</span>'+S.accel+'</small></div><div><small>'+S.stability+'</small><p lang="en">'+esc(track.selection)+'</p>'+seedScopeNote()+'</div></div>'+
'<p>'+S.release+'<span'+EN+'>'+esc(versionText(track.version))+'</span></p><p>'+S.protocolId+'<code>'+esc(track.protocolId)+'</code></p><p>'+S.audit+'<code>'+esc(track.auditSha)+'</code></p>'+
'<h3 class="detail-note">'+S.scope+'</h3><p>'+S.licence+'<span'+EN+'>'+esc(track.license)+'</span></p><div lang="en"><p>'+esc(track.attribution)+'</p><p>'+esc(track.rightsScope)+'</p></div>'+privacyNote()+'<p lang="en">'+esc(track.pretrainingOverlap)+'</p>'+coreExposureNote()+
'<a class="button" href="/data/'+track.id+'-protocol.json" download>'+S.dlProtocol+'</a> <a class="button" href="'+esc(track.source)+'" target="_blank" rel="noreferrer">'+S.original+'</a> <a class="button" href="'+esc(track.licenseUrl)+'" target="_blank" rel="noreferrer">'+S.licenceLink+'</a>'));
/* A v9 row's dialog: its figures, the exposure statement with its source, the
   row footnote, the export's notes and the weights licence (ZUNA 1.1's model-card
   sentence included), and where the whole row is printed. */
function fmDialog(r:FmRow){
  const t=fmOf(track.id),i=r.idle,tradeoff=track.type==='tradeoff';
  const orig=(o:string|null)=>o?'<span class="note-original" lang="en">'+esc(o)+'</span>':'';
  const figures=r.status!=='complete'||r.y===null||r.x===null?'<p class="detail-note"><strong>'+S.fmNotRun+'</strong> '+esc(r.reason??'')+orig(r.reasonOriginal)+'</p>'
    :'<div class="detail-metrics"><div><small>'+esc(metric(track.yLabel))+'</small><strong>'+pct(r.y)+'</strong><small>'+(tradeoff&&i?S.fmDetected(i.detected,i.commandTrials):r.interval?S.fmInterval(r.interval[0].toFixed(1),r.interval[1].toFixed(1)):'')+'</small></div>'+
     '<div><small>'+esc(metric(track.xLabel))+'</small><strong>'+(tradeoff?pct(r.x):r.x.toFixed(3))+'</strong><small>'+(tradeoff&&i?S.fmIdle(i.falseActivations,i.idleTrials):S.fmF1)+'</small></div></div>'+fmChance(r);
  show(r.name+' · '+titleOf(track),
    '<p><span'+EN+'>'+esc(r.mode)+'</span> · '+r.channels+' ch'+(r.subjects?' · '+r.subjects+S.participants:'')+'</p>'+figures+
    '<p class="detail-note">'+S.fmExposureLabel+esc(r.exposureText)+(r.exposureSource?' <a href="'+esc(r.exposureSource)+'" target="_blank" rel="noreferrer">'+S.fmSource+'</a>':'')+'</p>'+
    '<p class="detail-note">'+S.fmFootnote+esc(r.footnote)+orig(r.footnoteOriginal)+'</p>'+
    (r.notes?'<p class="detail-note" lang="en">'+esc(r.notes)+'</p>':'')+
    '<p class="detail-note">'+S.fmLicence+esc(r.licence)+orig(r.licenceOriginal)+'</p>'+
    (r.researchUse?'<p class="detail-note fm-research-use">'+S.fmResearchUse+'</p>':'')+
    '<p class="detail-note">'+S.fmFrozen+'</p>'+
    '<a class="button" href="'+esc(t.protocolHref)+'#foundation-v9">'+S.fmGroupLink+'</a> <a class="button" href="'+esc(r.href)+'">'+S.fmMethod+'</a> <a class="button" href="/data/'+esc(t.file)+'" download>'+S.fmCsv+'</a>');
}
/* LaBraM and CBraMod: the owner's sourced exposure statement (2026-10-04), beside
   the released sentence, which stays as released. */
function coreExposureNote(){
  const c=fmOf(track.id) as {coreExposure?:{text:string;urls:string[]}};
  if(!c.coreExposure)return '';
  return '<p class="detail-note fm-core-exposure">'+S.coreExposureLead+esc(c.coreExposure.text)+S.stop+c.coreExposure.urls.map(u=>'<a href="'+esc(u)+'" target="_blank" rel="noreferrer">'+S.fmSource+'</a>').join(' ')+' '+S.coreExposureTail+'</p>';
}
$('#result-rows').addEventListener('click',e=>{const button=(e.target as HTMLElement).closest<HTMLElement>('[data-model]');if(!button)return;
const fmId=button.dataset.model?.startsWith('fm:')?button.dataset.model.slice(3):null;
if(fmId!==null){const f=fmOf(track.id).rows.find(x=>x.id===fmId);if(f)fmDialog(f);return;}
const r=track.rows.find(r=>r.id===button.dataset.model)!;show(r.name+' · '+titleOf(track),
'<p><span'+EN+'>'+esc(r.mode)+'</span> · '+r.channels+' ch · '+r.subjects+S.participants+'</p><div class="detail-metrics"><div><small>'+esc(metric(track.yLabel))+'</small><strong>'+pct(r.y)+'</strong><small'+EN+'>'+esc(r.yDetail)+'</small></div><div><small>'+esc(metric(track.xLabel))+'</small><strong>'+xValue(r)+'</strong><small'+EN+'>'+esc(r.xDetail)+'</small></div></div><p lang="en">'+esc(r.note)+'</p>'+
(r.abstain!==null?'<p class="detail-note">'+S.abstainNote(r.subjects,r.abstain)+'</p>':'')+
'<p class="detail-note" lang="en">'+esc(r.modelRights)+'</p><p class="detail-note" lang="en">'+esc(track.limitation)+'</p><p class="detail-note">'+S.cohortOnly+'</p>');});
$('#ablation-rows').addEventListener('click',e=>{const button=(e.target as HTMLElement).closest<HTMLElement>('[data-model]');const id=button?.dataset.model?.startsWith('fm:')?button.dataset.model.slice(3):null;
const f=id===null?undefined:fmOf(track.id).rows.find(x=>x.id===id);if(f)fmDialog(f);});
$('#close-dialog').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
render();
const context=(document as Document & {modelContext?:{registerTool:(tool:object,options:object)=>unknown}}).modelContext;
if(context?.registerTool){const lifecycle=new AbortController();window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});try{void Promise.resolve(context.registerTool({name:'configure_eeg_comparison',title:'Configure EEG comparison',description:'Change the visible evaluation track and model family, and return the measured comparison. Does not train models or alter scores.',inputSchema:{type:'object',properties:{trackId:{type:'string',enum:data.tracks.map(t=>t.id)},family:{type:'string',enum:['all','foundation','small','classical']}},required:['trackId'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input:unknown){if(!input||typeof input!=='object')throw new Error('Expected an object');const value=input as Record<string,unknown>;if(Object.keys(value).some(k=>!['trackId','family'].includes(k))||typeof value.trackId!=='string'||!data.tracks.some(t=>t.id===value.trackId)||value.family!==undefined&&!['all','foundation','small','classical'].includes(String(value.family)))throw new Error('Invalid track or model family');$<HTMLSelectElement>('#family-filter').value=String(value.family??'all');selectTrack(value.trackId);return {trackId:track.id,status:track.status,models:[...visibleRows().map(r=>({name:r.name,primaryMetric:r.y,secondaryMetric:r.x})),
...visibleFm().map(r=>({name:r.name,primaryMetric:r.y,secondaryMetric:r.x,status:r.status==='complete'?'complete':'not run',release:fmData.release,pretrainingExposure:r.exposureText}))],limitation:track.limitation};}}, {signal:lifecycle.signal})).catch(()=>{});}catch{/* Unsupported experimental API leaves the regular controls usable. */}}
