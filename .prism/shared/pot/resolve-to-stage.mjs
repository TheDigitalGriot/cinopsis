// resolve-to-stage.mjs - turn the CONFIRMED rows of a potluck-stage resolve file into a stage file
// land-potluck-batch.mjs can land (same one path into the plan). needs-ruling and unresolved rows are
// left out on purpose: they stay open as rulings.
//   cat + tg: the sibling POT_T row from the same video when one exists, else the most common target
//   for the category in the plan; always strength 1 and noted "auto-mapped at close, retune".
//   node resolve-to-stage.mjs --plan <html> --resolve <resolve-YYYY-MM-DD.json> --cat <name=cat;...> --out <stage.json>
import fs from 'fs';
const argv = process.argv.slice(2);
const arg = k => { const i = argv.indexOf('--' + k); return i === -1 ? null : argv[i + 1]; };
const src = fs.readFileSync(arg('plan'), 'utf8');
const grab = (name, close) => { const i = src.indexOf('const ' + name + '='); const j = src.indexOf(close, i); return (0, eval)('(' + src.slice(i + name.length + 7, j + close.length - 1) + ')'); };
const POT = grab('POT_T', '}];'), VIDT = grab('VIDT', '};');
const R = JSON.parse(fs.readFileSync(arg('resolve'), 'utf8'));
const catOf = Object.fromEntries((arg('cat') || '').split(';').filter(Boolean).map(p => p.split('=')));
const lc = s => (s || '').toLowerCase();
const have = new Set(POT.map(r => lc(r.slug)));
const commonTg = cat => { const c = {}; for (const r of POT) if (r.cat === cat && r.tg[0]) c[r.tg[0][0]] = (c[r.tg[0][0]] || 0) + 1; return Object.entries(c).sort((a, b) => b[1] - a[1])[0][0]; };
const out = { batch: 'resolve-2026-10-15', source: arg('resolve'), videos: [], tools: [], vidt: {}, resolve: [], ossmeta: {}, unresolved: [] };
for (const x of R.items) {
  if (x.confidence !== 'confirmed' || !x.slug) { if (x.status !== 'resolved' || x.confidence !== 'confirmed') out.unresolved.push({ name: x.name, video: x.video, reason: (x.confidence || x.status) + ' - left open as a ruling' }); continue; }
  out.resolve.push({ n: x.name, r: x.slug, s: 'v', st: x.stars });
  if (have.has(lc(x.slug))) continue;
  const sib = POT.find(r => r.v === x.video && r.tg.length);
  const cat = catOf[x.name] || (sib && sib.cat);
  if (!cat) throw new Error('no cat for ' + x.name);
  const app = sib && sib.cat === cat ? sib.tg[0][0] : commonTg(cat);
  const how = sib && sib.cat === cat ? 'sibling row ' + sib.n : 'most common ' + cat + ' target';
  const title = VIDT[x.video] || '';
  out.tools.push({ n: x.name, slug: x.slug, cat, src: 'potluck:' + x.video, srcName: title, srcUrl: 'https://github.com/' + x.slug, v: x.video,
    b: (x.description || '').trim() + ' gh ' + R.generated + ': ' + x.stars + ' stars. Resolved from batch ' + x.batch + ' (' + x.lane + ' lane, ' + x.how + ').',
    tg: [[app, 1, 'auto-mapped at close from ' + how + ', retune']], decision: 'undecided', role: '', stage: 'later' });
  out.ossmeta[lc(x.slug)] = { cat, sn: title, su: 'https://github.com/' + x.slug, sc: 0 };
  have.add(lc(x.slug));
}
fs.writeFileSync(arg('out'), JSON.stringify(out, null, 1) + '\n', 'utf8');
console.log(JSON.stringify({ tools: out.tools.map(t => t.n + ':' + t.cat + ':' + t.tg[0][0]), resolve: out.resolve.length, leftOpen: out.unresolved.length }));
