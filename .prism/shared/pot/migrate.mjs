import fs from 'fs';
const PLACE=/^[—\-\s]*unverified|^[—\-\s]*hosted|^[—\-]\s/i;
function bounds(src,name){
  const re=new RegExp('(?:const|let|var)\\s+'+name+'\\s*=\\s*');
  const m=re.exec(src); if(!m) throw new Error('no '+name);
  const from=m.index+m[0].length;
  const a=src.indexOf('[',from), b=src.indexOf('{',from);
  let i=(a<0)?b:(b<0?a:Math.min(a,b));
  let depth=0,inS=false,q='',esc=false;
  for(let j=i;j<src.length;j++){const c=src[j];
    if(esc){esc=false;continue;}
    if(inS){if(c==='\\'){esc=true;}else if(c===q){inS=false;}continue;}
    if(c==='"'||c==="'"||c==='`'){inS=true;q=c;continue;}
    if(c==='['||c==='{')depth++;else if(c===']'||c==='}'){depth--;if(depth===0)return[i,j];}}
  throw new Error('unbalanced '+name);
}
let src=fs.readFileSync('base.html','utf8');
const raw=JSON.parse(fs.readFileSync('raw.json','utf8'));
const missing=JSON.parse(fs.readFileSync('missing.json','utf8'));
const items=JSON.parse(fs.readFileSync('items.json','utf8')).filter(x=>x.type==='oss-inspo');

// --- diagnostics on the placeholder class (report only, change nothing) ---
const place=items.filter(x=>!x.slug||PLACE.test(x.slug));
const realSlugs={}; items.filter(x=>x.slug&&!PLACE.test(x.slug)).forEach(x=>{const k=x.slug.toLowerCase();realSlugs[k]=(realSlugs[k]||0)+1;});
const trueDupes=Object.entries(realSlugs).filter(([,c])=>c>1);
console.log('DIAG oss-inspo items            :',items.length);
console.log('DIAG placeholder/no-slug items  :',place.length);
console.log('DIAG true duplicate real slugs  :',trueDupes.length, trueDupes.slice(0,8).map(d=>d[0]).join(', '));

// --- build the POT_T rows ---
const newRows=missing.map(t=>{
  const r={n:t.n, slug:t.slug||'', cat:t.cat||'devex', b:t.b||'',
           tg:Array.isArray(t.tg)?t.tg:[],
           decision:'undecided', role:'', stage:'later'};
  if(t.src){r.src=t.src;}
  if(t.srcName){r.srcName=t.srcName;}
  if(t.srcUrl){r.srcUrl=t.srcUrl;}
  const m=/^potluck:([A-Za-z0-9_\-]{6,})$/.exec(t.src||'');
  if(m && m[1]!=='scan') r.v=m[1];
  return r;
});
// --- splice into POT_T ---
let [pi,pj]=bounds(src,'POT_T');
const add=',\n'+newRows.map(r=>JSON.stringify(r)).join(',\n');
src=src.slice(0,pj)+add+src.slice(pj);
console.log('POT_T rows appended             :',newRows.length);

// --- OSSMETA / OSSMETA_N ---
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const metaAdd=[], metaNAdd=[];
for(const t of missing){
  const isScan=(t.src==='scan'||t.src==='potluck:scan');
  const e={cat:t.cat||'devex', sn:t.srcName||'', su:t.srcUrl||'', sc:isScan?1:0};
  if(t.slug && !PLACE.test(t.slug)){ if(!raw.OSSMETA[t.slug]) metaAdd.push([t.slug,e]); }
  else { const k=norm(t.n); if(k && !raw.OSSMETA_N[k]) metaNAdd.push([k,e]); }
}
function injectObj(name, pairs){
  if(!pairs.length) return;
  const [i,j]=bounds(src,name);
  const body=pairs.map(([k,v])=>JSON.stringify(k)+':'+JSON.stringify(v)).join(',\n');
  src=src.slice(0,j)+',\n'+body+src.slice(j);
}
injectObj('OSSMETA', metaAdd);
injectObj('OSSMETA_N', metaNAdd);
console.log('OSSMETA entries added           :',metaAdd.length);
console.log('OSSMETA_N entries added         :',metaNAdd.length);
fs.writeFileSync('out.html', src);
console.log('out.html bytes                  :', Buffer.byteLength(src,'utf8'));
