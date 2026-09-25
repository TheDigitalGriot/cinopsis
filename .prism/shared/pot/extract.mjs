import fs from 'fs';
const LIVE = process.env.LIVE;
function grab(src, name){
  const re = new RegExp('(?:const|let|var)\\s+'+name+'\\s*=\\s*');
  const m = re.exec(src); if(!m) return null;
  const from = m.index+m[0].length;
  const a = src.indexOf('[', from), b = src.indexOf('{', from);
  let i = (a<0) ? b : (b<0 ? a : Math.min(a,b));
  let depth=0, inS=false, q='', esc=false;
  for(let j=i;j<src.length;j++){
    const c=src[j];
    if(esc){esc=false;continue;}
    if(inS){ if(c==='\\'){esc=true;} else if(c===q){inS=false;} continue; }
    if(c==='"'||c==="'"||c==='`'){inS=true;q=c;continue;}
    if(c==='['||c==='{')depth++;
    else if(c===']'||c==='}'){depth--; if(depth===0) return src.slice(i,j+1);}
  }
  return null;
}
const plan = fs.readFileSync(LIVE+'/live/dgs-definitive-plan.html','utf8');
const shelf = fs.readFileSync(LIVE+'/live/griot-potluck-oss-repo.html','utf8');
const out = {};
for(const [k,src,name] of [['POT_T',plan,'POT_T'],['OSSMETA',plan,'OSSMETA'],['OSSMETA_N',plan,'OSSMETA_N'],['POT_VIDEOS',plan,'POT_VIDEOS'],['POT_APPS',plan,'POT_APPS'],['T',shelf,'T']]){
  const s = grab(src,name);
  if(!s){ out[k]=null; continue; }
  out[k] = eval('('+s+')');
}
fs.writeFileSync('raw.json', JSON.stringify(out));
const norm = s => String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const pot = out.POT_T||[];
const potSlug = new Set(pot.filter(x=>x.slug).map(x=>x.slug.toLowerCase()));
const potName = new Set(pot.map(x=>norm(x.n)));
const missing = (out.T||[]).filter(t=>{
  if(t.slug && potSlug.has(t.slug.toLowerCase())) return false;
  if(potName.has(norm(t.n))) return false;
  return true;
});
console.log('POT_T rows      :', pot.length);
console.log('shelf T rows    :', (out.T||[]).length);
console.log('OSSMETA keys    :', out.OSSMETA?Object.keys(out.OSSMETA).length:'MISSING');
console.log('OSSMETA_N keys  :', out.OSSMETA_N?Object.keys(out.OSSMETA_N).length:'MISSING');
console.log('POT_VIDEOS      :', out.POT_VIDEOS?out.POT_VIDEOS.length:'MISSING');
console.log('POT_APPS        :', out.POT_APPS?out.POT_APPS.length:'MISSING');
console.log('MISSING from POT_T:', missing.length);
console.log('  with slug     :', missing.filter(m=>m.slug).length);
console.log('  no slug       :', missing.filter(m=>!m.slug).length);
const cats={}; missing.forEach(m=>cats[m.cat||'(none)']=(cats[m.cat||'(none)']||0)+1);
console.log('  by cat        :', JSON.stringify(cats));
const srcs={}; missing.forEach(m=>srcs[m.src||'(none)']=(srcs[m.src||'(none)']||0)+1);
console.log('  by src        :', JSON.stringify(srcs));
console.log('  sample        :', missing.slice(0,5).map(m=>m.n+' ['+(m.slug||'no-slug')+']').join(' | '));
fs.writeFileSync('missing.json', JSON.stringify(missing,null,1));
