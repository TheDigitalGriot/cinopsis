import fs from 'fs';
const LIVE=process.env.LIVE;
function grab(src,name){
  const re=new RegExp('(?:const|let|var)\\s+'+name+'\\s*=\\s*');
  const m=re.exec(src); if(!m) return null;
  const from=m.index+m[0].length;
  const a=src.indexOf('[',from), b=src.indexOf('{',from);
  let i=(a<0)?b:(b<0?a:Math.min(a,b));
  let depth=0,inS=false,q='',esc=false;
  for(let j=i;j<src.length;j++){const c=src[j];
    if(esc){esc=false;continue;}
    if(inS){if(c==='\\'){esc=true;}else if(c===q){inS=false;}continue;}
    if(c==='"'||c==="'"||c==='`'){inS=true;q=c;continue;}
    if(c==='['||c==='{')depth++;else if(c===']'||c==='}'){depth--;if(depth===0)return src.slice(i,j+1);}}
  return null;
}
const plan=fs.readFileSync(LIVE+'/live/dgs-definitive-plan.html','utf8');
const ITEMS=eval('('+grab(plan,'ITEMS')+')');
fs.writeFileSync('items.json',JSON.stringify(ITEMS));
const oss=ITEMS.filter(x=>x.type==='oss-inspo');
const raw=JSON.parse(fs.readFileSync('raw.json','utf8'));
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const potSlug=new Set(raw.POT_T.filter(x=>x.slug).map(x=>x.slug.toLowerCase()));
const potName=new Set(raw.POT_T.map(x=>norm(x.n)));
const missing=JSON.parse(fs.readFileSync('missing.json','utf8'));
const missSlug=new Set(missing.filter(x=>x.slug).map(x=>x.slug.toLowerCase()));
const missName=new Set(missing.map(x=>norm(x.n)));
const orphan=oss.filter(it=>{
  const s=(it.slug||'').toLowerCase(), n=norm(it.oss||it.item);
  if(s&&(potSlug.has(s)||missSlug.has(s)))return false;
  if(potName.has(n)||missName.has(n))return false;
  return true;
});
console.log('ITEMS total        :',ITEMS.length);
console.log('oss-inspo items    :',oss.length);
console.log('POT_T now          :',raw.POT_T.length);
console.log('POT_T after migrate:',raw.POT_T.length+missing.length);
console.log('oss-inspo ORPHANS (no POT_T row, even after migration):',orphan.length);
console.log(orphan.slice(0,20).map(o=>(o.oss||o.item)+' ['+(o.slug||'no-slug')+'] app='+o.app).join('\n'));
fs.writeFileSync('orphans.json',JSON.stringify(orphan,null,1));
const sc={}; Object.values(raw.OSSMETA).forEach(v=>sc[v.sc]=(sc[v.sc]||0)+1);
console.log('OSSMETA sc values  :',JSON.stringify(sc));
