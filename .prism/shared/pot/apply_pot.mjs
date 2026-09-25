import fs from 'fs';
function bounds(src,name){
  const re=new RegExp('(?:const|let|var)\\s+'+name+'\\s*=\\s*');
  const m=re.exec(src); if(!m) throw new Error('no '+name);
  const from=m.index+m[0].length;
  const a=src.indexOf('[',from), b=src.indexOf('{',from);
  let i=(a<0)?b:(b<0?a:Math.min(a,b));
  let d=0,inS=false,q='',esc=false;
  for(let j=i;j<src.length;j++){const c=src[j];
    if(esc){esc=false;continue;}
    if(inS){if(c==='\\'){esc=true;}else if(c===q){inS=false;}continue;}
    if(c==='"'||c==="'"||c==='`'){inS=true;q=c;continue;}
    if(c==='['||c==='{')d++;else if(c===']'||c==='}'){d--;if(d===0)return[i,j];}}
  throw new Error('unbalanced '+name);
}
let src=fs.readFileSync('base2.html','utf8');
const P=JSON.parse(fs.readFileSync('pot_new_rows.json','utf8'));
const appId = n => n.toLowerCase().replace(/[^a-z0-9]/g,'');
// 1) POT_T rows
{const [i,j]=bounds(src,'POT_T');
 src = src.slice(0,j) + ',\n' + P.rows.map(r=>JSON.stringify(r)).join(',\n') + src.slice(j);}
// 2) paired oss-inspo ITEMS - the 1:1 derived mirror, one per new POT_T row
{const items = P.rows.map(r=>{
   const strongest = r.tg.slice().sort((a,b)=>b[1]-a[1])[0];
   const secondary = r.tg.length>1 ? ' Also touches ' + r.tg.slice(1).map(t=>t[0]).join(', ') + '.' : '';
   return {app: appId(strongest[0]), item: r.n, type:'oss-inspo',
           detail: r.b + secondary, src: r.src, status:'idea', stage:'later',
           oss: r.n, slug: r.slug, decision:'undecided', role:''};
 });
 const [i,j]=bounds(src,'ITEMS');
 src = src.slice(0,j) + ',\n' + items.map(x=>JSON.stringify(x)).join(',\n') + src.slice(j);}
// 3) OSSMETA / OSSMETA_N
function inject(name, obj){
  const keys=Object.keys(obj); if(!keys.length) return;
  const [i,j]=bounds(src,name);
  src = src.slice(0,j) + ',\n' + keys.map(k=>JSON.stringify(k)+':'+JSON.stringify(obj[k])).join(',\n') + src.slice(j);
}
inject('OSSMETA', P.meta);
inject('OSSMETA_N', P.metan);
fs.writeFileSync('out2.html', src);
// verify
function grab(s,name){const [i,j]=bounds(s,name);return s.slice(i,j+1);}
const v=fs.readFileSync('out2.html','utf8');
const POT=eval('('+grab(v,'POT_T')+')'), IT=eval('('+grab(v,'ITEMS')+')');
const M=eval('('+grab(v,'OSSMETA')+')'), N=eval('('+grab(v,'OSSMETA_N')+')');
console.log('POT_T     1328 ->', POT.length);
console.log('ITEMS     1857 ->', IT.length);
console.log('oss-inspo 1341 ->', IT.filter(x=>x.type==='oss-inspo').length);
console.log('OSSMETA    899 ->', Object.keys(M).length);
console.log('OSSMETA_N 1055 ->', Object.keys(N).length);
const bad=POT.filter(r=>!r.n||r.cat===undefined||!Array.isArray(r.tg)||r.decision===undefined||!r.stage);
console.log('POT_T schema failures:', bad.length);
console.log('bytes:', Buffer.byteLength(v,'utf8'));
