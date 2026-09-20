import data from '../data/mvp.json';
type Track=typeof data.tracks[number];
type Row=Track['rows'][number];
const $=<T extends HTMLElement=HTMLElement>(s:string)=>document.querySelector<T>(s)!;
const esc=(s:unknown)=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
let track:Track=data.tracks[0];
/* Warm series, deliberately with no blue in it: slate blue is reserved for the
   chance reference line, which must never read as one more model. */
const colors=['#b3450e','#1f6f63','#8a6d1f','#7a4a8c','#a8382f','#5c7a2e','#93552a','#6b3f5e'];
const CHANCE_LINE='#2f5f74';
const pct=(v:number)=>v.toFixed(1)+'%';
const xValue=(r:Row)=>track.type==='tradeoff'?pct(r.x):r.x.toFixed(3);

/** Seed-sensitivity record, present on the two tracks that were re-run. */
type SeedSensitivity={model:string;seeds:number[];balancedAccuracyPercent:number[];meanPercent:number;sampleSdPercentagePoints:number};
const seedInfo=(t:Track)=>(t as Partial<{seedSensitivity:SeedSensitivity}>).seedSensitivity;

/** Where the displayed (original-seed) value sits among the seeds actually run. */
function seedRank(ss:SeedSensitivity){
  const v=ss.balancedAccuracyPercent,shown=v[0],hi=Math.max(...v),lo=Math.min(...v);
  return {shown,hi,lo,word:shown>=hi?'highest':shown<=lo?'lowest':'middle'};
}

/* The headline number on these rows is one seed. Saying so only inside the
   protocol dialog left the table looking like a settled measurement, so the
   condition travels with the number instead. */
function seedFlag(r:Row){
  const ss=seedInfo(track);
  if(!ss||ss.model!==r.name)return '';
  const {hi,lo,word}=seedRank(ss);
  return '<span class="flag seed">Single seed — the '+word+' of '+ss.balancedAccuracyPercent.length+
    ' run ('+lo.toFixed(2)+'–'+hi.toFixed(2)+'%, mean '+ss.meanPercent.toFixed(2)+'%)</span>';
}

/* A zero false-activation rate produced by participants who always abstain is
   not reliability. The count was only in the model dialog; it belongs next to
   the 0.0% a reader is scanning. */
function abstainFlag(r:Row){
  if(track.type!=='tradeoff'||!r.abstain)return '';
  return '<span class="flag">'+r.abstain+' of '+r.subjects+' participants always abstained</span>';
}

/* `scope` already carries the clearest statement of why the retained seed is the
   retained one. It was sitting unused in the data while the weaker sentence was
   the only thing shown, which is the reverse of what a sceptical reader needs —
   on both seed-tested tracks the retained value is also the highest of the three. */
function seedScopeNote(){
  const ss=seedInfo(track) as (SeedSensitivity&{scope?:string})|undefined;
  if(!ss)return '';
  const {word}=seedRank(ss);
  return '<p class="detail-note">'+esc(ss.scope??'')+' On this metric the retained seed is also the '+word+
    ' of the three; the seed was fixed and audited before the other two were run.</p>';
}

const chanceOf=(t:Track)=>(t as Partial<{chanceLevel:number|null}>).chanceLevel ?? null;

/* Several rows sit at or below chance once their interval is taken into
   account. Chance was only ever stated inside the protocol, so a 49.4% on a
   50%-chance task read like an ordinary score. */
function chanceFlag(r:Row){
  const c=chanceOf(track);
  if(c===null||track.type==='tradeoff')return '';
  const iv=(r as Partial<{interval:number[]|null}>).interval;
  if(r.y<=c)return '<span class="flag">At or below the '+c+'% chance level</span>';
  if(iv&&iv[0]<=c)return '<span class="flag">Interval reaches the '+c+'% chance level</span>';
  return '';
}
/* All eight protocols are listed as tabs rather than hidden in a <select>, so
   the shape of the release is visible before anything is chosen. Roving
   tabindex keeps the group a single stop in the tab order. */
const tabs=[...document.querySelectorAll<HTMLElement>('.track-tab')];
function syncTabs(){
  $('#track-tabs').setAttribute('data-active',track.id);
  $('#track-panel').setAttribute('aria-labelledby','tab-'+track.id);
  for(const b of tabs){const on=b.dataset.track===track.id;b.setAttribute('aria-selected',on?'true':'false');b.tabIndex=on?0:-1;}
}

const dialog=$<HTMLDialogElement>('#detail-dialog');
function show(title:string,body:string){$('#dialog-title').textContent=title;$('#dialog-body').innerHTML=body;dialog.showModal();}
function visibleRows(){const f=$<HTMLSelectElement>('#family-filter').value,s=$<HTMLSelectElement>('#sort-results').value;return track.rows.filter(r=>f==='all'||r.family===f).slice().sort((a,b)=>s==='y-desc'?b.y-a.y:s==='x-asc'?(track.type==='tradeoff'?a.x-b.x:b.x-a.x):a.name.localeCompare(b.name));}
function render(){
const rows=visibleRows();
$('#track-title').textContent=track.subtitle;
$('#track-meta').textContent=track.dataset+' · '+track.subjects+' subjects · '+track.observations+' · '+track.exposure;
$('#track-limitation').textContent=track.limitation;
$('#track-rights').textContent=track.license+' · Aggregate research results';
$<HTMLAnchorElement>('#track-source').href=track.source;
syncTabs();
$('#secondary-sort').textContent=track.type==='tradeoff'?'Secondary metric ↑':'Secondary metric ↓';
$('#metric-y-heading').textContent=track.yLabel;$('#metric-x-heading').textContent=track.xLabel;
$<HTMLAnchorElement>('#download-results').href='/data/'+track.id+'-results.csv';
$('#result-rows').innerHTML=rows.length?rows.map(r=>'<tr><td><button class="model-name" data-model="'+esc(r.id)+'">'+esc(r.name)+' ↗</button><small>'+esc(r.mode)+' · '+r.channels+' ch</small></td><td><strong>'+pct(r.y)+'</strong><small>'+esc(r.yDetail)+'</small>'+chanceFlag(r)+seedFlag(r)+'</td><td><strong>'+xValue(r)+'</strong><small>'+esc(r.xDetail)+'</small>'+abstainFlag(r)+'</td><td>'+r.seconds.toFixed(1)+'s</td></tr>').join(''):'<tr><td colspan="4" class="empty">No evaluated models from this family in this track. Try another family.</td></tr>';
draw(rows);
hint();
}
/* Only advertise horizontal scrolling when there is something to reach. */
function hint(){
const box=$('.table-panel .scroll'),el=$('#scroll-hint');
if(box.scrollWidth>box.clientWidth+1)el.setAttribute('data-overflow','');else el.removeAttribute('data-overflow');
}
window.addEventListener('resize',hint);
function draw(rows:Row[]){
const tradeoff=track.type==='tradeoff';
$('#chart-title').textContent=tradeoff?'Detection meets reliability':'Accuracy by configuration';
const chanceNote=chanceOf(track);
$('#chart-note').textContent=tradeoff?'Upper left is better. Always abstaining also yields zero false activations, so detection must be read alongside them.':'Subject-mean balanced accuracy. Error bars show descriptive 95% intervals where available.'+(chanceNote!==null?' The dashed line marks the '+chanceNote+'% chance level for this task.':' See the protocol for chance level.');
$('#chart-legend').innerHTML=rows.map((r,i)=>'<span><i style="background:'+colors[i%colors.length]+'"></i>'+esc(r.name)+'</span>').join('');
if(!rows.length){$('#result-chart').innerHTML='<p class="empty">No results to display</p>';return;}
const x0=38,y0=176,w=210,h=145;
let svg='<svg viewBox="0 0 280 220" role="img" aria-label="'+esc(track.yLabel)+' and '+esc(track.xLabel)+' chart">';
[0,25,50,75,100].forEach(v=>{const y=y0-h*v/100;svg+='<line x1="'+x0+'" x2="'+(x0+w)+'" y1="'+y+'" y2="'+y+'" stroke="#e7dccd"/><text x="29" y="'+(y+4)+'" text-anchor="end">'+v+'</text>';});
if(tradeoff){const maxX=Math.max(5,...rows.map(r=>r.x))*1.2;
[0,maxX/2,maxX].forEach(v=>{const x=x0+w*v/maxX;svg+='<text x="'+x+'" y="195" text-anchor="middle">'+v.toFixed(1)+'%</text>';});
rows.forEach((r,i)=>{const x=x0+w*r.x/maxX,y=y0-h*r.y/100;svg+='<circle cx="'+x+'" cy="'+y+'" r="5" fill="'+colors[i%colors.length]+'" stroke="#fffdfa" stroke-width="1.5"><title>'+esc(r.name)+': detection '+pct(r.y)+', false activation '+pct(r.x)+'</title></circle>';});
svg+='<text x="145" y="216" text-anchor="middle">Idle false activation rate →</text><text x="38" y="16">Command detection % ↑</text>';
}else{const gap=w/rows.length,chance=chanceOf(track);
// Without this line a 10.8% on a 40-class task and a 49.4% on a 2-class task
// look equally unremarkable against 0/25/50/75/100 gridlines.
// Named in the note rather than on the line: at 2.5% chance the label would sit
// on top of the bars, and the note has room to say what the line means.
if(chance!==null){const cy=y0-h*chance/100;
svg+='<line x1="'+x0+'" x2="'+(x0+w)+'" y1="'+cy+'" y2="'+cy+'" stroke="'+CHANCE_LINE+'" stroke-width="1.2" stroke-dasharray="5 3"/>';}
rows.forEach((r,i)=>{const x=x0+gap*(i+.5),height=h*r.y/100;svg+='<rect x="'+(x-gap*.25)+'" y="'+(y0-height)+'" width="'+gap*.5+'" height="'+height+'" rx="2" fill="'+colors[i%colors.length]+'"><title>'+esc(r.name)+'：'+pct(r.y)+'</title></rect><text x="'+x+'" y="'+(y0-height-7)+'" text-anchor="middle">'+r.y.toFixed(1)+'</text><text x="'+x+'" y="195" text-anchor="middle">'+(i+1)+'</text>';if('interval' in r&&Array.isArray(r.interval)){const [a,b]=r.interval;svg+='<path d="M'+x+','+(y0-h*a/100)+'V'+(y0-h*b/100)+' M'+(x-4)+','+(y0-h*a/100)+'h8 M'+(x-4)+','+(y0-h*b/100)+'h8" stroke="#241c15" stroke-width="1"/>';}});
svg+='<text x="38" y="16">Balanced accuracy % ↑</text><text x="145" y="216" text-anchor="middle">Configurations follow legend order</text>';
}$('#result-chart').innerHTML=svg+'</svg>';
}
function selectTrack(id:string){const found=data.tracks.find(t=>t.id===id);if(!found)throw new Error('Unknown track');track=found;$('#track-panel').setAttribute('aria-label',track.title+' results');render();}
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
/* A column heading in the coverage matrix opens that protocol below. The href
   still works without JavaScript; it just lands on the default protocol. */
$('#overview').addEventListener('click',e=>{const a=(e.target as HTMLElement).closest<HTMLElement>('[data-jump]');if(a?.dataset.jump)selectTrack(a.dataset.jump);});
$('#family-filter').addEventListener('change',render);$('#sort-results').addEventListener('change',render);
$('#open-protocol').addEventListener('click',()=>show(track.title+' · Protocol',
'<p>'+esc(track.subtitle)+'</p><ol>'+track.protocol.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol>'+
'<div class="detail-metrics"><div><small>Scoring stage sum</small><strong>'+track.elapsed.toFixed(1)+' seconds</strong><small>'+esc(track.backend)+' · may include accelerator waiting</small></div><div><small>Configuration stability</small><p>'+esc(track.selection)+'</p>'+seedScopeNote()+'</div></div>'+
'<p>Dataset release: '+esc(track.version)+'</p><p>Protocol: <code>'+esc(track.protocolId)+'</code></p><p>Audit record SHA256: <code>'+esc(track.auditSha)+'</code></p>'+
'<h3 class="detail-note">Source and permitted scope</h3><p>'+esc(track.attribution)+'</p><p>'+esc(track.rightsScope)+'</p><p>'+esc(track.privacyReview)+'</p><p>'+esc(track.pretrainingOverlap)+'</p>'+
'<a class="button" href="/data/'+track.id+'-protocol.json" download>Download protocol · JSON ↓</a> <a class="button" href="'+esc(track.source)+'" target="_blank" rel="noreferrer">Original dataset ↗</a> <a class="button" href="'+esc(track.licenseUrl)+'" target="_blank" rel="noreferrer">'+esc(track.license)+' ↗</a>'));
$('#result-rows').addEventListener('click',e=>{const button=(e.target as HTMLElement).closest<HTMLElement>('[data-model]');if(!button)return;const r=track.rows.find(r=>r.id===button.dataset.model)!;show(r.name+' · '+track.title,
'<p>'+esc(r.mode)+' · '+r.channels+' ch · '+r.subjects+' participants</p><div class="detail-metrics"><div><small>'+esc(track.yLabel)+'</small><strong>'+pct(r.y)+'</strong><small>'+esc(r.yDetail)+'</small></div><div><small>'+esc(track.xLabel)+'</small><strong>'+xValue(r)+'</strong><small>'+esc(r.xDetail)+'</small></div></div><p>'+esc(r.note)+'</p>'+
(r.abstain!==null?'<p class="detail-note">Of '+r.subjects+' participants, '+r.abstain+' selected an always-abstain threshold on calibration data. Their test trials remain in the denominator.</p>':'')+
'<p class="detail-note">'+esc(r.modelRights)+'</p><p class="detail-note">'+esc(track.limitation)+'</p><p class="detail-note">Only cohort aggregates are shared. Individual scores, recordings and predictions remain local.</p>');});
$('#close-dialog').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
render();
const context=(document as Document & {modelContext?:{registerTool:(tool:object,options:object)=>unknown}}).modelContext;
if(context?.registerTool){const lifecycle=new AbortController();window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});try{void Promise.resolve(context.registerTool({name:'configure_eeg_comparison',title:'Configure EEG comparison',description:'Change the visible evaluation track and model family, and return the measured comparison. Does not train models or alter scores.',inputSchema:{type:'object',properties:{trackId:{type:'string',enum:data.tracks.map(t=>t.id)},family:{type:'string',enum:['all','foundation','small','classical']}},required:['trackId'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input:unknown){if(!input||typeof input!=='object')throw new Error('Expected an object');const value=input as Record<string,unknown>;if(Object.keys(value).some(k=>!['trackId','family'].includes(k))||typeof value.trackId!=='string'||!data.tracks.some(t=>t.id===value.trackId)||value.family!==undefined&&!['all','foundation','small','classical'].includes(String(value.family)))throw new Error('Invalid track or model family');$<HTMLSelectElement>('#family-filter').value=String(value.family??'all');selectTrack(value.trackId);return {trackId:track.id,status:track.status,models:visibleRows().map(r=>({name:r.name,primaryMetric:r.y,secondaryMetric:r.x})),limitation:track.limitation};}}, {signal:lifecycle.signal})).catch(()=>{});}catch{/* Unsupported experimental API leaves the regular controls usable. */}}
